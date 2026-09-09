"""Rótulo de risco de evasão a partir do gap relativo, fórmula definida pela Visão."""
from __future__ import annotations

import pandas as pd

# Threshold final: gap_relativo acima disso marca o veículo como em risco. Único
# lugar do código onde esse valor deve ser alterado.
#
# Escolhido como 2.0 depois de comparar 1.2 / 1.5 / 2.0 (issue de sensibilidade de
# threshold). AUC e precision@top-K saturam perto de 1.0 nos três — não servem de
# critério, porque em_risco é definido a partir do próprio gap_relativo (o modelo
# só recupera essa regra, não aprende sinal novo). O critério decisivo foi a
# plausibilidade da distribuição (issue "validar distribuição do rótulo"):
#   threshold=1.2 -> 90,2% da frota em risco no geral, 10/20 modelos >=90%
#   threshold=1.5 -> 82,7% da frota em risco no geral, 9/20 modelos >=90%
#   threshold=2.0 -> 72,3% da frota em risco no geral, 8/20 modelos >=90%
# 2.0 é o único dos três que tira ECOSPORT (16 mil VINs) da faixa >=90% e reduz a
# taxa geral para uma faixa mais plausível como sinal de priorização (não "quase
# todo mundo é risco"). Os modelos que continuam >=90% em 2.0 são a KA (94,8%,
# modelo descontinuado pela Ford no Brasil - efeito genuíno, não artefato do
# threshold) e modelos de amostra muito pequena (<=125 VINs) que qualquer
# threshold deixaria perto de 100%/0% por ruído estatístico, não por escolha de corte.
GAP_RELATIVO_THRESHOLD = 2.0

# Nº mínimo de serviços para o VIN ter "gap histórico próprio" (dias desde o último
# serviço comparado ao intervalo do modelo). Abaixo disso (ex.: só 1 serviço), não há
# padrão de retorno estabelecido para esse VIN — usa-se o fallback por idade do veículo.
MIN_SERVICOS_PARA_GAP_PROPRIO = 2


def compute_em_risco(
    gap_relativo: pd.Series, threshold: float = GAP_RELATIVO_THRESHOLD
) -> pd.Series:
    """em_risco = gap_relativo > threshold.

    `gap_relativo` nulo (ex.: VIN sem intervalo mediano do modelo) produz `em_risco`
    nulo (`pd.NA`) — risco desconhecido, não "sem risco".
    """
    em_risco = (gap_relativo > threshold).astype("boolean")
    em_risco[gap_relativo.isna()] = pd.NA

    return em_risco.rename("em_risco")


def add_em_risco(
    df: pd.DataFrame,
    gap_relativo_col: str = "gap_relativo",
    threshold: float = GAP_RELATIVO_THRESHOLD,
    output_col: str = "em_risco",
) -> pd.DataFrame:
    """Adiciona a coluna `em_risco` a uma cópia de `df`. `df` não é modificado."""
    result = df.copy()
    result[output_col] = compute_em_risco(result[gap_relativo_col], threshold=threshold)

    return result


def compute_gap_com_fallback(
    gap_relativo: pd.Series,
    idade_dias: pd.Series,
    intervalo_mediano_esperado: pd.Series,
    n_servicos: pd.Series,
    intervalo_mediano_geral: float | None = None,
    min_servicos_para_gap_proprio: int = MIN_SERVICOS_PARA_GAP_PROPRIO,
) -> pd.Series:
    """Gap relativo com fallback para VINs sem gap histórico próprio (ex.: 1 único serviço).

    Regra (25% dos VINs só têm 1 serviço — não dá para calcular gap histórico próprio
    para eles):
    - `n_servicos >= min_servicos_para_gap_proprio`: usa `gap_relativo` (dias desde o
      último serviço ÷ intervalo esperado do modelo) — o VIN já tem um padrão de
      retorno próprio estabelecido.
    - Caso contrário: usa `idade_dias / intervalo_mediano_esperado` como sinal
      alternativo — compara há quanto tempo o veículo foi vendido/entregue com o
      intervalo de manutenção esperado do modelo.
    - Se ainda restar nulo depois disso (ex.: modelo do VIN sem intervalo mediano
      computável), usa `idade_dias / intervalo_mediano_geral` como último recurso,
      quando esse valor for informado — garante que nenhum VIN fique sem sinal de risco.

    Divisão por um intervalo igual a 0 produz nulo (não infinito), como em
    `build_vehicle_features.compute_gap_relativo`.
    """
    def _safe_ratio(numerador: pd.Series, denominador: pd.Series) -> pd.Series:
        denominador_seguro = denominador.mask(denominador == 0)
        return numerador / denominador_seguro

    gap_fallback_modelo = _safe_ratio(idade_dias, intervalo_mediano_esperado)

    tem_gap_proprio = n_servicos >= min_servicos_para_gap_proprio
    resultado = gap_relativo.where(tem_gap_proprio, gap_fallback_modelo)

    if intervalo_mediano_geral:
        gap_fallback_geral = idade_dias / intervalo_mediano_geral
        resultado = resultado.fillna(gap_fallback_geral)

    return resultado.rename("gap_com_fallback")


def apply_low_volume_heuristic(
    df: pd.DataFrame,
    gap_col: str = "gap_com_fallback",
    threshold: float = GAP_RELATIVO_THRESHOLD,
    output_col: str = "em_risco",
) -> pd.DataFrame:
    """Heurística de risco para modelos de veículo com poucos dados: `em_risco = gap > threshold`,
    sem treinar um modelo de ML.

    Para modelos de baixo volume (ex.: os que não são RANGER/KA — ver issues de
    segmentação por modelo), não há VINs suficientes para treinar/validar um
    classificador com confiança. Isso não é uma perda de qualidade: as issues de
    RANGER e KA mostraram que um modelo de ML dedicado dá a **mesma AUC** da
    heurística pura, porque `em_risco` já É essa regra (`gap > threshold`) — treinar
    um modelo só recupera a regra que já temos. Reaproveita `add_em_risco` (mesma
    função usada em toda a base) em vez de duplicar a lógica do threshold; `df` não
    é modificado.
    """
    return add_em_risco(df, gap_relativo_col=gap_col, threshold=threshold, output_col=output_col)
