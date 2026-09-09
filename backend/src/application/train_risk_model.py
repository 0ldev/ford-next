"""Split temporal de treino/teste para o modelo de risco de evasão.

Split temporal (em vez de aleatório) simula a situação real de produção: o modelo é
treinado só com o passado e avaliado contra dados que, na época do treino, ainda não
tinham acontecido.
"""
from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

TRAIN_FRACTION_PADRAO = 0.8

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
