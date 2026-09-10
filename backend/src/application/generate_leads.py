"""Ranking de veículos por score de risco dentro de cada concessionária (DealerCode)."""
from __future__ import annotations

import pandas as pd

from src.application.train_risk_model import RiskClassifier
from src.domain.risk_label import apply_low_volume_heuristic

# RANGER e KA são os únicos modelos de veículo com VINs suficientes para validar um
# classificador de ML com confiança (ver `risk_label.apply_low_volume_heuristic` e as
# issues de segmentação por modelo/comparação modelo-específico vs. geral). Para os
# demais modelos, `compute_score_risco` usa a heurística de threshold em vez do score
# do modelo treinado.
MODELOS_COM_VOLUME_SUFICIENTE_PARA_ML: tuple[str, ...] = ("RANGER", "KA")


def compute_score_risco(
    df: pd.DataFrame,
    modelo: RiskClassifier,
    feature_columns: tuple[str, ...],
    model_col: str = "ModelName",
    modelos_com_ml: tuple[str, ...] = MODELOS_COM_VOLUME_SUFICIENTE_PARA_ML,
    output_col: str = "score_risco",
) -> pd.DataFrame:
    """Score de risco por VIN, segmentado por volume de dados do modelo do veículo.

    VINs de `modelos_com_ml` (RANGER/KA por padrão) recebem a probabilidade do
    `modelo` de ML treinado (`predict_proba`). Os demais recebem
    `risk_label.apply_low_volume_heuristic` (mesma regra de threshold do rótulo
    `em_risco`, sem ML — não há VINs suficientes para validar um classificador com
    confiança para eles) convertida para 0.0/1.0, mantendo `output_col` na mesma
    escala [0, 1] nos dois casos. Seguro para `df` sem nenhuma linha em um dos dois
    segmentos (ex.: subconjunto filtrado por concessionária) — não chama
    `predict_proba`/`apply_low_volume_heuristic` em uma seleção vazia.

    `df` não é modificado.
    """
    result = df.copy()
    tem_volume_para_ml = result[model_col].isin(modelos_com_ml)

    if tem_volume_para_ml.any():
        result.loc[tem_volume_para_ml, output_col] = modelo.predict_proba(
            result.loc[tem_volume_para_ml, list(feature_columns)]
        )[:, 1]

    sem_volume_para_ml = ~tem_volume_para_ml
    if sem_volume_para_ml.any():
        heuristica = apply_low_volume_heuristic(result.loc[sem_volume_para_ml])
        result.loc[sem_volume_para_ml, output_col] = heuristica["em_risco"].astype(float)

    return result


def rank_by_dealer(
    df: pd.DataFrame,
    dealer_col: str = "DealerCode",
    score_col: str = "score_risco",
    rank_col: str = "rank_concessionaria",
) -> pd.DataFrame:
    """Ranqueia os veículos por `score_col` dentro de cada `dealer_col`.

    Rank 1 = maior score (maior risco) daquela concessionária. Empates recebem o
    mesmo rank (`method="min"`), sem pular posições de forma inconsistente.

    `df` não é modificado. Retorna uma cópia ordenada por `dealer_col` e depois por
    `rank_col` crescente — pronta para consumo direto (ex.: "top 5 leads de cada
    concessionária").
    """
    result = df.copy()
    result[rank_col] = (
        result.groupby(dealer_col)[score_col].rank(method="min", ascending=False).astype(int)
    )

    return result.sort_values([dealer_col, rank_col]).reset_index(drop=True)


def explain_risk(dias_desde_ultimo_servico: float, gap_relativo: float) -> str:
    """Monta a frase explicando o motivo do risco de um veículo.

    Ex.: `explain_risk(180, 1.4)` -> "180 dias sem serviço, 40% acima do intervalo
    esperado do modelo". `gap_relativo` <= 1 é descrito como "dentro do intervalo
    esperado" ou "X% abaixo", em vez de forçar uma leitura de "acima" incorreta.

    Retorna uma frase genérica (sem quebrar) se algum dos dois valores for nulo.
    """
    if pd.isna(dias_desde_ultimo_servico) or pd.isna(gap_relativo):
        return "dados insuficientes para explicar o risco deste veículo"

    dias = round(dias_desde_ultimo_servico)
    sufixo_dias = "dia" if dias == 1 else "dias"

    percentual = round((gap_relativo - 1) * 100)
    if percentual > 0:
        comparativo = f"{percentual}% acima do intervalo esperado do modelo"
    elif percentual < 0:
        comparativo = f"{abs(percentual)}% abaixo do intervalo esperado do modelo"
    else:
        comparativo = "dentro do intervalo esperado do modelo"

    return f"{dias} {sufixo_dias} sem serviço, {comparativo}"


def add_risk_explanation(
    df: pd.DataFrame,
    dias_col: str = "dias_desde_ultimo_servico",
    gap_col: str = "gap_com_fallback",
    output_col: str = "motivo_risco",
) -> pd.DataFrame:
    """Adiciona a coluna `output_col` com a frase de `explain_risk` para cada linha de `df`.

    Default de `gap_col` é `gap_com_fallback`, não `gap_relativo` — é a coluna que
    efetivamente alimenta `FEATURE_COLUMNS`/`score_risco` (`train_risk_model.py`). Para
    os VINs que caem no fallback (1 único serviço, ~29% da base), `gap_relativo` fica
    nulo e não é o número que gerou o score; citar ele no motivo explicaria uma decisão
    diferente da que o modelo/heurística realmente tomou.

    `df` não é modificado.
    """
    result = df.copy()
    result[output_col] = result.apply(
        lambda linha: explain_risk(linha[dias_col], linha[gap_col]), axis=1
    )

    return result
