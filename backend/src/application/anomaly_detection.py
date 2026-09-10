"""Detecção de anomalias no histórico de serviços — schema de GET /api/anomalies.

Três tipos, cada um com sua própria regra e limiar — heurísticas simples e
documentadas, não uma análise de sensibilidade completa (diferente do threshold de
`risk_label.GAP_RELATIVO_THRESHOLD`, que teve uma issue inteira dedicada a calibrá-lo).
Os limiares aqui são números redondos defensáveis, não valores calibrados contra o
dataset — ajustar se a demo mostrar ruído demais ou de menos.

Nota sobre `pico_mainsource`: os únicos valores de `MainSource` neste dataset já são
todos "oficiais" (`"Agenda + Official Maintenance"`, `"Official Maintenance"`, e
variações com `"+ GUDB"`) — não existe uma categoria de "oficina independente" para
detectar migração de fato. O proxy usado é a fração de serviços SEM o prefixo
"Agenda" (ou seja, atendido sem passar pelo agendamento oficial do app/sistema) — um
sinal real de mudança no mix de canal de atendimento, não de evasão da rede Ford.
"""
from __future__ import annotations

import pandas as pd

from src.application.trend_metrics import compute_monthly_share

JANELA_MESES = 3
MIN_SERVICOS_DEALER = 100
MIN_SERVICOS_MODELO = 200
QUEDA_MIN_PCT = 20.0
QUEDA_MIN_BASE_PCT = 3.0
GAP_MIN_PONTOS = 5.0
PICO_MIN_PONTOS = 3.0
MAX_POR_TIPO = 5


def _competencias_completas(df: pd.DataFrame, service_date_col: str = "ServiceDate") -> list[str]:
    """Competências "YYYY-MM" disponíveis, descartando a última se estiver truncada.

    O último mês de um snapshot às vezes cobre só alguns dias (este dataset termina
    em 2026-05-04, por exemplo — ~350 ordens contra ~11-12 mil nos meses cheios).
    Comparar contra um mês truncado produziria uma "queda" em massa só por o mês
    ainda não ter terminado quando o snapshot foi tirado, não por evasão real.
    Descartamos o último mês quando seu volume é menos da metade da média dos 3
    meses anteriores.
    """
    historico = df.dropna(subset=[service_date_col])
    contagem = historico[service_date_col].dt.to_period("M").astype(str).value_counts().sort_index()
    competencias = list(contagem.index)

    if len(competencias) >= 4:
        media_anteriores = contagem.iloc[-4:-1].mean()
        if media_anteriores > 0 and contagem.iloc[-1] < media_anteriores / 2:
            competencias = competencias[:-1]

    return competencias


def _janela_recente_e_anterior(
    competencias: list[str], janela: int = JANELA_MESES
) -> tuple[list[str], list[str]] | None:
    """Os últimos `janela` meses ("recente") e os `janela` antes deles ("anterior").

    `None` se não houver competências suficientes (2×`janela`) para comparar com
    confiança — evita declarar "queda" a partir de 1-2 meses de histórico.
    """
    if len(competencias) < janela * 2:
        return None

    return competencias[-janela:], competencias[-2 * janela : -janela]


def detect_dealer_share_drops(
    df: pd.DataFrame,
    min_servicos: int = MIN_SERVICOS_DEALER,
    janela: int = JANELA_MESES,
    queda_min_pct: float = QUEDA_MIN_PCT,
    base_min_pct: float = QUEDA_MIN_BASE_PCT,
    limite: int = MAX_POR_TIPO,
) -> list[dict]:
    """Concessionárias com queda abrupta de VIN Share — tipo `"queda_dealer"`.

    Compara a média do VIN Share (todos os modelos) nos últimos `janela` meses
    completos contra a média dos `janela` meses antes deles, por concessionária.
    Só considera dealers com pelo menos `min_servicos` ordens de serviço na vida
    toda — dealers minúsculos oscilam demais para uma "queda" ter algum significado.
    Também exige que a média anterior (`base`) seja pelo menos `base_min_pct`: perto
    de zero, uma diferença de poucos VINs já produz uma "queda" relativa de 100% sem
    nenhum significado real (ex.: 0,1% → 0,0%). Retorna as `limite` maiores quedas,
    ordenadas por severidade desc.

    `entidade` é o `DealerCode` (texto): este dataset não tem uma tabela de nomes de
    concessionária, só o código.
    """
    janelas = _janela_recente_e_anterior(_competencias_completas(df), janela)
    if janelas is None:
        return []
    recente, anterior = janelas

    volume_por_dealer = df.groupby("DealerCode").size()
    dealers_elegiveis = volume_por_dealer[volume_por_dealer >= min_servicos].index.tolist()
    if not dealers_elegiveis:
        return []

    tabela = pd.DataFrame(compute_monthly_share(df, group_col="DealerCode", grupos=dealers_elegiveis))

    media_recente = tabela[tabela["competencia"].isin(recente)].groupby("DealerCode")["valor"].mean()
    media_anterior = tabela[tabela["competencia"].isin(anterior)].groupby("DealerCode")["valor"].mean()

    resultado = []
    for dealer in dealers_elegiveis:
        base = media_anterior.get(dealer, 0.0)
        atual = media_recente.get(dealer, 0.0)
        if base < base_min_pct:
            continue

        queda_pct = (base - atual) / base * 100
        if queda_pct < queda_min_pct:
            continue

        resultado.append({
            "tipo": "queda_dealer",
            "entidade": str(dealer),
            "severidade": round(min(queda_pct / 100, 1.0), 2),
            "descricao": (
                f"Queda de {queda_pct:.0f}% no VIN Share nos últimos {janela} meses "
                f"({base:.1f}% para {atual:.1f}%)."
            ),
        })

    resultado.sort(key=lambda item: item["severidade"], reverse=True)
    return resultado[:limite]


def detect_model_gaps(
    df: pd.DataFrame,
    min_servicos: int = MIN_SERVICOS_MODELO,
    janela: int = JANELA_MESES,
    gap_min_pontos: float = GAP_MIN_PONTOS,
    limite: int = MAX_POR_TIPO,
) -> list[dict]:
    """Modelos com VIN Share consistentemente abaixo da média da rede — tipo `"gap_modelo"`.

    Compara a média do VIN Share de cada modelo nos últimos `janela` meses contra a
    média da rede (todos os modelos) no mesmo período. Só considera modelos com pelo
    menos `min_servicos` ordens de serviço na vida toda.
    """
    historico = df.dropna(subset=["ServiceDate"])
    competencias_completas = _competencias_completas(df)
    janelas = _janela_recente_e_anterior(competencias_completas, janela)
    if janelas is None:
        return []
    recente, _ = janelas

    total_elegiveis_rede = historico["VIN_Hash"].nunique()
    competencia = historico["ServiceDate"].dt.to_period("M").astype(str)
    com_servico_rede_por_mes = historico.assign(competencia=competencia).groupby("competencia")["VIN_Hash"].nunique()
    valor_rede_por_mes = com_servico_rede_por_mes / total_elegiveis_rede * 100 if total_elegiveis_rede else com_servico_rede_por_mes * 0
    media_rede = valor_rede_por_mes.reindex(recente).mean()
    if pd.isna(media_rede):
        return []

    volume_por_modelo = df.groupby("ModelName").size()
    modelos_elegiveis = volume_por_modelo[volume_por_modelo >= min_servicos].index.tolist()
    if not modelos_elegiveis:
        return []

    tabela_modelo = pd.DataFrame(compute_monthly_share(df, group_col="ModelName", grupos=modelos_elegiveis))
    media_por_modelo = (
        tabela_modelo[tabela_modelo["competencia"].isin(recente)].groupby("ModelName")["valor"].mean()
    )
    frota_por_modelo = historico.groupby("ModelName")["VIN_Hash"].nunique()

    resultado = []
    for modelo in modelos_elegiveis:
        valor_modelo = media_por_modelo.get(modelo, 0.0)
        gap_pontos = media_rede - valor_modelo
        if gap_pontos < gap_min_pontos:
            continue

        resultado.append({
            "tipo": "gap_modelo",
            "entidade": modelo,
            "severidade": round(min(gap_pontos / 30, 1.0), 2),
            "descricao": (
                f"{valor_modelo:.1f}% de VIN Share, {gap_pontos:.1f} pontos abaixo da média da "
                f"rede ({media_rede:.1f}%). Frota de {int(frota_por_modelo.get(modelo, 0)):,} veículos."
            ),
        })

    resultado.sort(key=lambda item: item["severidade"], reverse=True)
    return resultado[:limite]


def detect_mainsource_spikes(
    df: pd.DataFrame,
    min_servicos: int = MIN_SERVICOS_DEALER,
    janela: int = JANELA_MESES,
    pico_min_pontos: float = PICO_MIN_PONTOS,
    limite: int = MAX_POR_TIPO,
) -> list[dict]:
    """Concessionárias com aumento no mix de serviços fora do agendamento oficial —
    tipo `"pico_mainsource"`. Ver ressalva sobre `MainSource` no docstring do módulo.

    Comparação em pontos percentuais (não relativa): perto de zero, uma taxa que sobe
    de 0,3% para 1,0% já é um aumento relativo de mais de 200% sem representar uma
    mudança real de padrão — `pico_min_pontos` filtra esse ruído (ver mesma lógica em
    `detect_dealer_share_drops`/`base_min_pct`).
    """
    historico = df.dropna(subset=["ServiceDate", "MainSource"]).copy()
    janelas = _janela_recente_e_anterior(_competencias_completas(historico), janela)
    if janelas is None:
        return []
    recente, anterior = janelas

    volume_por_dealer = historico.groupby("DealerCode").size()
    dealers_elegiveis = volume_por_dealer[volume_por_dealer >= min_servicos].index.tolist()
    if not dealers_elegiveis:
        return []

    historico["competencia"] = historico["ServiceDate"].dt.to_period("M").astype(str)
    historico["sem_agenda"] = ~historico["MainSource"].str.startswith("Agenda")

    taxa = (
        historico[historico["DealerCode"].isin(dealers_elegiveis)]
        .groupby(["DealerCode", "competencia"])["sem_agenda"]
        .mean()
        .mul(100)
    )

    resultado = []
    for dealer in dealers_elegiveis:
        atual = taxa.reindex([(dealer, mes) for mes in recente]).mean()
        base = taxa.reindex([(dealer, mes) for mes in anterior]).mean()
        if pd.isna(base) or pd.isna(atual):
            continue

        aumento_pontos = atual - base
        if aumento_pontos < pico_min_pontos:
            continue

        resultado.append({
            "tipo": "pico_mainsource",
            "entidade": str(dealer),
            "severidade": round(min(aumento_pontos / 20, 1.0), 2),
            "descricao": (
                f"Aumento de {aumento_pontos:.1f} pontos na proporção de serviços fora do "
                f"agendamento oficial ({base:.1f}% para {atual:.1f}% das ordens)."
            ),
        })

    resultado.sort(key=lambda item: item["severidade"], reverse=True)
    return resultado[:limite]


def compute_anomalies(df: pd.DataFrame) -> list[dict]:
    """Todas as anomalias detectadas — schema de `GET /api/anomalies`."""
    return [
        *detect_dealer_share_drops(df),
        *detect_model_gaps(df),
        *detect_mainsource_spikes(df),
    ]
