"""PROTÓTIPO (branch `prototype`, não mesclado em `master`): rótulo de risco normalizado
pelo padrão de CADA veículo, em vez de comparado só ao intervalo mediano do modelo.

Hipótese: comparar "dias desde o último serviço" contra a mediana do MODELO inteiro
superestima risco para veículos com timing naturalmente errático (alta variância
própria), mesmo que sejam clientes fiéis — é um artefato de amostragem (paradoxo da
inspeção / length bias: um snapshot no tempo tende a "pegar" veículos no meio de um
intervalo mais longo que o normal, com mais frequência que num intervalo curto), não
sinal de evasão real.

Aqui, veículos com histórico suficiente (3+ serviços, mesma exigência de
`build_vehicle_features.compute_service_count_and_gap_std`) são comparados contra o
PRÓPRIO padrão (média e desvio padrão dos seus gaps), não contra o padrão do modelo
inteiro. Isso não elimina o length bias (o "dias desde o último serviço" observado
continua sendo uma amostra enviesada), mas corrige o principal sintoma: veículos com
timing naturalmente mais variável deixam de ser penalizados só por serem mais
variáveis — eles são comparados à própria variância, não à variância do modelo.
"""
from __future__ import annotations

import pandas as pd


def compute_vehicle_own_gap_stats(
    df: pd.DataFrame,
    vin_col: str = "VIN_Hash",
    service_date_col: str = "ServiceDate",
) -> pd.DataFrame:
    """Por VIN: média e desvio padrão dos intervalos entre serviços consecutivos.

    Exige 3+ serviços (2+ intervalos) para as duas colunas não ficarem nulas — mesma
    regra de `build_vehicle_features.compute_service_count_and_gap_std` (sai de graça
    do `mean`/`std` amostral do pandas sobre 0 ou 1 intervalo válido).

    `df` não é modificado. Retorna uma linha por VIN, colunas
    `[vin_col, "media_gap_proprio", "desvio_padrao_gaps"]`.
    """
    dados = df.dropna(subset=[service_date_col]).sort_values([vin_col, service_date_col])
    intervalo_dias = dados.groupby(vin_col)[service_date_col].diff().dt.days

    media = intervalo_dias.groupby(dados[vin_col]).mean().rename("media_gap_proprio")
    desvio = intervalo_dias.groupby(dados[vin_col]).std().rename("desvio_padrao_gaps")

    return pd.concat([media, desvio], axis=1).reset_index()


def compute_gap_zscore(
    dias_desde_ultimo_servico: pd.Series,
    media_gap_proprio: pd.Series,
    desvio_padrao_gaps: pd.Series,
) -> pd.Series:
    """Z-score do gap atual em relação ao padrão do PRÓPRIO veículo.

    `> 0` significa "mais tempo sem serviço do que o normal para este veículo
    específico" — independe de como o modelo inteiro se comporta.

    Nulo quando não há desvio padrão próprio (menos de 3 serviços) ou quando o desvio
    é 0 (histórico perfeitamente regular — qualquer desvio já representaria um número
    infinito de desvios-padrão, um caso que o z-score não consegue expressar de forma
    útil; cai para o fallback por modelo, ver `compute_em_risco_hibrido`).
    """
    desvio_seguro = desvio_padrao_gaps.mask(desvio_padrao_gaps == 0)
    return ((dias_desde_ultimo_servico - media_gap_proprio) / desvio_seguro).rename("gap_zscore")


def compute_em_risco_hibrido(
    gap_zscore: pd.Series,
    gap_com_fallback: pd.Series,
    threshold_zscore: float = 1.5,
    threshold_gap_fallback: float = 2.0,
) -> pd.Series:
    """`em_risco`: usa o z-score próprio quando disponível, senão cai para o rótulo por modelo.

    Combina os dois sinais em vez de escolher um só — preserva o fallback já existente
    em produção (`risk_label.compute_gap_com_fallback`) para VINs sem histórico próprio
    suficiente (1-2 serviços, ~29% da base), e só troca o critério primário para os
    veículos que TÊM histórico suficiente para ter um baseline pessoal.

    `threshold_zscore=1.5` é um ponto de partida (1,5 desvio padrão acima da própria
    média), não uma escolha testada como o `GAP_RELATIVO_THRESHOLD=2.0` de produção —
    é exatamente o que este protótipo existe para calibrar.
    """
    usa_proprio = gap_zscore.notna()
    em_risco = pd.Series(pd.NA, index=gap_zscore.index, dtype="boolean")

    em_risco[usa_proprio] = gap_zscore[usa_proprio] > threshold_zscore
    em_risco[~usa_proprio] = gap_com_fallback[~usa_proprio] > threshold_gap_fallback

    return em_risco.rename("em_risco_hibrido")
