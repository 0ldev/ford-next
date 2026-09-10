"""Série temporal mensal de VIN share, agregada por um grupo (modelo, concessionária etc.)."""
from __future__ import annotations

import pandas as pd

# ~20 anos de meses. Acima disso quase certamente e' erro de input (periodoInicio/
# periodoFim invertidos ou digitados errado), nao caso de uso real do dashboard.
MAX_COMPETENCIAS = 240


def listar_competencias(inicio: str, fim: str) -> list[str]:
    """Lista de competências "YYYY-MM" entre `inicio` e `fim`, inclusive.

    Intervalo invertido (`inicio` depois de `fim`) produz lista vazia, sem erro —
    `pd.period_range` já se comporta assim.
    """
    intervalo = pd.period_range(start=inicio, end=fim, freq="M")
    if len(intervalo) > MAX_COMPETENCIAS:
        raise ValueError(
            f"Intervalo de {len(intervalo)} meses excede o limite de {MAX_COMPETENCIAS} "
            "(~20 anos) — confira periodoInicio/periodoFim."
        )

    return [str(periodo) for periodo in intervalo]


def compute_monthly_share(
    df: pd.DataFrame,
    group_col: str,
    grupos: list[str] | None = None,
    periodo_inicio: str | None = None,
    periodo_fim: str | None = None,
    vin_col: str = "VIN_Hash",
    service_date_col: str = "ServiceDate",
) -> list[dict]:
    """VIN share (%) mensal por `group_col` (ex.: "ModelName" ou "DealerCode").

    Elegível (denominador) por grupo = total de VINs distintos que já tiveram QUALQUER
    serviço registrado naquele grupo, em toda a história disponível — mesmo conceito de
    "elegível" de `vin_share_metrics.compute_vin_share`, só que aqui o agrupamento já é
    o próprio filtro (não há filtro de idade/dealer adicional). "Com serviço"
    (numerador), por (grupo, mês) = VINs distintos daquele grupo com ao menos 1 serviço
    naquele mês.

    Importante para `group_col="DealerCode"`: um VIN pode ter sido atendido em vários
    dealers ao longo da vida, então o elegível é "todo VIN que já teve ao menos 1
    serviço naquele dealer" (`nunique` por grupo), não "o dealer da primeira linha do
    VIN" — isso contaria só 1 dealer por VIN e subestimaria todos os outros que ele
    também visitou. Para `group_col="ModelName"` (1 modelo fixo por VIN) dá no mesmo
    resultado de qualquer forma, então a mesma conta serve para os dois casos.

    Meses sem nenhum serviço para um grupo entram com `valor=0.0` (não ficam ausentes)
    — essencial para o gráfico de tendência não ter buracos silenciosos.

    `grupos` restringe e ordena as séries retornadas (na ordem dada); ausente = todos
    os grupos presentes no histórico, em ordem alfabética — incluindo um `grupo`
    inexistente no histórico produz uma série de zeros, não erro. `periodo_inicio`/
    `periodo_fim` ("YYYY-MM") default para o primeiro/último mês com dado disponível.

    Retorna uma lista de dicts `{group_col: ..., "competencia": "YYYY-MM", "valor": float}`.
    """
    historico = df.dropna(subset=[service_date_col])

    total_elegiveis_por_grupo = historico.groupby(group_col)[vin_col].nunique().to_dict()

    # `.dt.to_period("M")` é vetorizado; `.dt.strftime("%Y-%m")` cai para formatação
    # elemento a elemento em Python e é ~15x mais lento nas ~535 mil linhas do
    # histórico (1,65s vs 0,11s, medido) — o suficiente para estourar qualquer
    # orçamento de latência do endpoint.
    competencia = historico[service_date_col].dt.to_period("M").astype(str)
    com_servico_por_grupo_mes = (
        historico.assign(competencia=competencia)
        .groupby([group_col, "competencia"])[vin_col]
        .nunique()
        .to_dict()
    )

    competencias_disponiveis = sorted(competencia.unique())
    inicio = periodo_inicio or (competencias_disponiveis[0] if competencias_disponiveis else None)
    fim = periodo_fim or (competencias_disponiveis[-1] if competencias_disponiveis else None)
    competencias = listar_competencias(inicio, fim) if inicio and fim else []

    grupos_considerados = list(grupos) if grupos else sorted(historico[group_col].dropna().unique())

    pontos = []
    for grupo in grupos_considerados:
        elegiveis = total_elegiveis_por_grupo.get(grupo, 0)
        for mes in competencias:
            com_servico = com_servico_por_grupo_mes.get((grupo, mes), 0)
            valor = round(com_servico / elegiveis * 100, 1) if elegiveis else 0.0
            pontos.append({group_col: grupo, "competencia": mes, "valor": valor})

    return pontos


def compute_trend(
    df: pd.DataFrame,
    modelos: list[str] | None = None,
    periodo_inicio: str | None = None,
    periodo_fim: str | None = None,
) -> list[dict]:
    """Série temporal de VIN share por modelo — schema de `GET /api/trend`.

    Wrapper de `compute_monthly_share` agrupando por `ModelName`, com as colunas já
    renomeadas para o contrato do front-end: `{"data": "YYYY-MM", "valor": float, "categoria": modelo}`.
    """
    pontos = compute_monthly_share(
        df,
        group_col="ModelName",
        grupos=modelos,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
    )

    return [
        {"data": ponto["competencia"], "valor": ponto["valor"], "categoria": ponto["ModelName"]}
        for ponto in pontos
    ]
