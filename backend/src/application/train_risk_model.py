"""Split temporal de treino/teste para o modelo de risco de evasão.

Split temporal (em vez de aleatório) simula a situação real de produção: o modelo é
treinado só com o passado e avaliado contra dados que, na época do treino, ainda não
tinham acontecido.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from src.domain.risk_label import compute_em_risco

TRAIN_FRACTION_PADRAO = 0.8

# Thresholds de gap_relativo comparados na análise de sensibilidade do rótulo.
THRESHOLDS_COMPARACAO_PADRAO: tuple[float, ...] = (1.2, 1.5, 2.0)

# Features numéricas usadas para prever em_risco, selecionadas da tabela de features
# das issues anteriores. gap_com_fallback é o gap relativo já com fallback por idade
# (issue "fallback para VINs com 1 serviço") — sem isso, VINs com 1 serviço entrariam
# como NaN e seriam descartados do treino/teste.
FEATURE_COLUMNS: tuple[str, ...] = ("idade_dias", "gap_com_fallback", "n_servicos")
TARGET_COLUMN = "em_risco"

# Profundidade máxima baixa (3-4): mantém a árvore rasa/interpretável e reduz risco de
# overfitting — é o modelo alternativo ao baseline linear (LogisticRegression).
TREE_MAX_DEPTH_PADRAO = 4
RANDOM_STATE_PADRAO = 42

RiskClassifier = Pipeline | DecisionTreeClassifier


def compute_cutoff_date(dates: pd.Series, train_fraction: float = TRAIN_FRACTION_PADRAO) -> pd.Timestamp:
    """Data de corte: o quantil `train_fraction` de `dates` (nulos são ignorados).

    Com `train_fraction=0.8` (padrão), é a data que deixa ~80% das datas, em ordem
    cronológica, antes ou igual a ela.
    """
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction deve estar entre 0 e 1 (exclusive)")

    return dates.dropna().quantile(train_fraction)


def temporal_train_test_split(
    df: pd.DataFrame,
    date_col: str,
    train_fraction: float = TRAIN_FRACTION_PADRAO,
    cutoff_date: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """Split temporal: treino = `date_col` ≤ `cutoff_date`; teste = `date_col` > `cutoff_date`.

    Ordena por `date_col` antes de particionar. Se `cutoff_date` não for informado,
    usa `compute_cutoff_date(df[date_col], train_fraction)` — por padrão, ~80% do
    período mais antigo vai para o treino. Linhas com `date_col` nulo são descartadas
    (não dá pra posicionar uma linha sem data no tempo). `df` não é modificado.

    Retorna `(treino, teste, cutoff_date)` — o `cutoff_date` é devolvido para
    auditoria/log, junto da data usada no split.
    """
    dados = df.dropna(subset=[date_col]).sort_values(date_col)

    if cutoff_date is None:
        cutoff_date = compute_cutoff_date(dados[date_col], train_fraction)

    treino = dados[dados[date_col] <= cutoff_date].copy()
    teste = dados[dados[date_col] > cutoff_date].copy()

    return treino, teste, cutoff_date


def _feature_matrix_e_alvo(
    df: pd.DataFrame, feature_columns: tuple[str, ...], target_column: str
) -> tuple[pd.DataFrame, pd.Series]:
    """Monta X, y descartando linhas com feature ou alvo nulo (scikit-learn não aceita NaN)."""
    dados = df.dropna(subset=[*feature_columns, target_column])
    X = dados[list(feature_columns)]
    y = dados[target_column].astype("boolean").astype(int)

    return X, y


def train_logistic_regression(
    treino: pd.DataFrame,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
) -> Pipeline:
    """Treina uma LogisticRegression (com padronização das features) em `treino`.

    Linhas com alguma feature ou o alvo nulo são descartadas do treino. `treino` não
    é modificado.
    """
    X_treino, y_treino = _feature_matrix_e_alvo(treino, feature_columns, target_column)

    modelo = make_pipeline(StandardScaler(), LogisticRegression())
    modelo.fit(X_treino, y_treino)

    return modelo


def train_decision_tree(
    treino: pd.DataFrame,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
    max_depth: int = TREE_MAX_DEPTH_PADRAO,
    random_state: int = RANDOM_STATE_PADRAO,
) -> DecisionTreeClassifier:
    """Treina uma DecisionTreeClassifier rasa (max_depth baixo) em `treino`.

    Alternativa não linear ao baseline `train_logistic_regression`, para o mesmo
    problema e as mesmas features — profundidade baixa (3-4) evita overfitting e
    mantém a árvore pequena o bastante para inspecionar visualmente. Linhas com
    alguma feature ou o alvo nulo são descartadas do treino. `treino` não é modificado.
    """
    X_treino, y_treino = _feature_matrix_e_alvo(treino, feature_columns, target_column)

    modelo = DecisionTreeClassifier(max_depth=max_depth, random_state=random_state)
    modelo.fit(X_treino, y_treino)

    return modelo


def evaluate_auc(
    modelo: RiskClassifier,
    teste: pd.DataFrame,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
) -> float:
    """AUC (ROC) do `modelo` no conjunto de teste. Linhas com feature/alvo nulo são descartadas.

    Funciona com qualquer classificador scikit-learn que exponha `predict_proba`
    (`train_logistic_regression` ou `train_decision_tree`).
    """
    X_teste, y_teste = _feature_matrix_e_alvo(teste, feature_columns, target_column)
    y_proba = modelo.predict_proba(X_teste)[:, 1]

    return roc_auc_score(y_teste, y_proba)


def precision_at_top_k(y_true: pd.Series, y_score: np.ndarray, k_fraction: float) -> float:
    """Precision@top-K: entre os `k_fraction` (ex.: 10%) com maior `y_score`, qual fração
    realmente tem `y_true`=1.

    `k` é `ceil(n * k_fraction)`, com mínimo de 1 linha. Em empate de score, a ordem de
    desempate segue a ordem original (estável) — não afeta a métrica agregada.
    """
    if not 0 < k_fraction <= 1:
        raise ValueError("k_fraction deve estar entre 0 (exclusive) e 1 (inclusive)")

    y_true_array = np.asarray(y_true)
    y_score_array = np.asarray(y_score)

    n = len(y_true_array)
    k = max(1, math.ceil(n * k_fraction))

    top_k_idx = np.argsort(-y_score_array, kind="stable")[:k]

    return float(y_true_array[top_k_idx].mean())


def evaluate_precision_at_k(
    modelo: RiskClassifier,
    teste: pd.DataFrame,
    k_fraction: float,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
) -> float:
    """Precision@top-`k_fraction` do `modelo` no conjunto de teste.

    Ranqueia `teste` pelo score do modelo (`predict_proba`) e mede a precisão nos
    `k_fraction` de maior score — ex.: `k_fraction=0.1` responde "dos 10% de veículos
    com maior score, quantos realmente estão marcados `em_risco`?".
    """
    X_teste, y_teste = _feature_matrix_e_alvo(teste, feature_columns, target_column)
    y_proba = modelo.predict_proba(X_teste)[:, 1]

    return precision_at_top_k(y_teste, y_proba, k_fraction)


def compare_thresholds(
    treino: pd.DataFrame,
    teste: pd.DataFrame,
    thresholds: tuple[float, ...] = THRESHOLDS_COMPARACAO_PADRAO,
    gap_col: str = "gap_com_fallback",
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Sensibilidade do modelo a diferentes thresholds do rótulo de risco.

    Para cada threshold em `thresholds`: recalcula `target_column` = `compute_em_risco`
    sobre `gap_col` (mesma regra de `src.domain.risk_label`), re-treina uma
    LogisticRegression do zero em `treino` e avalia AUC + precision@top-10%/20% em
    `teste`. `treino`/`teste` não são modificados (o rótulo recalculado vive em cópias).

    Retorna uma linha por threshold com `[threshold, pct_em_risco_treino,
    pct_em_risco_teste, auc, precision_top10, precision_top20]`.
    """
    linhas = []

    for threshold in thresholds:
        treino_rotulado = treino.assign(**{target_column: compute_em_risco(treino[gap_col], threshold=threshold)})
        teste_rotulado = teste.assign(**{target_column: compute_em_risco(teste[gap_col], threshold=threshold)})

        modelo = train_logistic_regression(treino_rotulado, feature_columns, target_column)

        linhas.append({
            "threshold": threshold,
            "pct_em_risco_treino": treino_rotulado[target_column].mean(),
            "pct_em_risco_teste": teste_rotulado[target_column].mean(),
            "auc": evaluate_auc(modelo, teste_rotulado, feature_columns, target_column),
            "precision_top10": evaluate_precision_at_k(modelo, teste_rotulado, 0.10, feature_columns, target_column),
            "precision_top20": evaluate_precision_at_k(modelo, teste_rotulado, 0.20, feature_columns, target_column),
        })

    return pd.DataFrame(linhas)
