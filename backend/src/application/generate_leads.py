"""Ranking de veículos por score de risco dentro de cada concessionária (DealerCode)."""
from __future__ import annotations

import pandas as pd


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
    gap_col: str = "gap_relativo",
    output_col: str = "motivo_risco",
) -> pd.DataFrame:
    """Adiciona a coluna `output_col` com a frase de `explain_risk` para cada linha de `df`.

    `df` não é modificado.
    """
    result = df.copy()
    result[output_col] = result.apply(
        lambda linha: explain_risk(linha[dias_col], linha[gap_col]), axis=1
    )

    return result
