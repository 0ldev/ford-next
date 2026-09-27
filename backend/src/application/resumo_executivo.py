"""Resumo executivo — visão geral para GET /api/resumo-executivo.

Não é um dado novo: é uma seleção enxuta (top 3) sobre dados já calculados em
`anomaly_detection` e `leads_repository`, pensada para "bateu o olho, já sei o que
fazer" — o dashboard inteiro tem muito mais detalhe, isso aqui é só o atalho pra
onde olhar primeiro.
"""
from __future__ import annotations

import pandas as pd

from src.application.anomaly_detection import _competencias_completas
from src.application.trend_metrics import compute_monthly_share

LIMITE_PADRAO = 3
MIN_LEADS_MODELO = 200
LIMIAR_ALTO_RISCO = 0.7  # mesma escala de severidade de `frontend/domain/severidade.ts`

# Este dataset começa em 2020-01 com ~19 ordens no mês, subindo pra milhares só a
# partir de 2021 (rampa de adoção do histórico, não evasão) — "elegível" olha a vida
# toda do VIN, então os primeiros meses têm o mesmo denominador dos maduros só que
# quase nenhum numerador ainda, e "viram" artificialmente os piores meses do dataset
# inteiro. Restringe a busca aos últimos `JANELA_MESES_CHURN` meses (rede já madura)
# pra não confundir início de coleta de dado com evasão real.
JANELA_MESES_CHURN = 24


def concessionarias_em_alerta(anomalias: list[dict], limite: int = LIMITE_PADRAO) -> list[dict]:
    """As concessionárias com o alerta mais severo — `queda_dealer` ou `pico_mainsource`.

    Uma concessionária pode aparecer nos dois tipos (queda de VIN Share E aumento de
    serviço fora do agendamento); mantém só o pior dos dois por dealer, para o resumo
    não repetir a mesma unidade duas vezes com números diferentes.
    """
    candidatas = [a for a in anomalias if a["tipo"] in ("queda_dealer", "pico_mainsource")]

    pior_por_dealer: dict[str, dict] = {}
    for anomalia in candidatas:
        atual = pior_por_dealer.get(anomalia["entidade"])
        if atual is None or anomalia["severidade"] > atual["severidade"]:
            pior_por_dealer[anomalia["entidade"]] = anomalia

    ranking = sorted(pior_por_dealer.values(), key=lambda item: item["severidade"], reverse=True)

    return [
        {
            "dealerCode": item["entidade"],
            "tipo": item["tipo"],
            "severidade": item["severidade"],
            "resumo": item["resumo"],
        }
        for item in ranking[:limite]
    ]


def modelos_maior_risco(
    leads: pd.DataFrame, min_leads: int = MIN_LEADS_MODELO, limiar_alto: float = LIMIAR_ALTO_RISCO, limite: int = LIMITE_PADRAO
) -> list[dict]:
    """Modelos com maior % da frota em risco alto (`score >= limiar_alto`).

    `leads` é o `leads.csv` inteiro (um score por VIN da frota, não só o top da
    fila) — a % é sobre o total de veículos daquele modelo, não sobre a rede toda.
    Só considera modelos com pelo menos `min_leads` veículos: um modelo raro com
    poucas unidades vira 0%/100% ao sabor de 1-2 VINs, sem significado real (mesma
    lógica de piso de amostra pequena usada nas anomalias e no ranking por dealer).
    """
    total_por_modelo = leads.groupby("modelo").size()
    elegiveis = total_por_modelo[total_por_modelo >= min_leads].index

    if len(elegiveis) == 0:
        return []

    alto_risco_por_modelo = leads[leads["score"] >= limiar_alto].groupby("modelo").size()

    resultado = [
        {
            "modelo": modelo,
            "percentualAltoRisco": round(int(alto_risco_por_modelo.get(modelo, 0)) / int(total_por_modelo[modelo]) * 100, 1),
            "totalVeiculos": int(total_por_modelo[modelo]),
        }
        for modelo in elegiveis
    ]
    resultado.sort(key=lambda item: item["percentualAltoRisco"], reverse=True)

    return resultado[:limite]


def meses_maior_churn(
    historico: pd.DataFrame, limite: int = LIMITE_PADRAO, janela_meses: int = JANELA_MESES_CHURN
) -> list[dict]:
    """Os meses com o menor VIN Share da rede inteira (maior evasão aparente).

    Mesmo conceito de "elegível"/"com serviço" de `compute_monthly_share`, só que
    agrupado pela rede inteira (1 grupo só) em vez de por modelo/dealer — dá a
    linha de base pra saber se um mês ruim é sazonalidade da rede toda ou um
    problema isolado de uma concessionária/modelo específico. Descarta o último
    mês se estiver truncado (mesmo motivo de `anomaly_detection._competencias_completas`:
    um mês parcial parece uma queda que não é real) e restringe a busca aos últimos
    `janela_meses` — sem isso, o início do histórico (rede ainda não madura) sempre
    "venceria" o ranking por ser baixo por razão errada (ver `JANELA_MESES_CHURN`).
    """
    competencias_completas = _competencias_completas(historico)
    if not competencias_completas:
        return []
    competencias_validas = set(competencias_completas[-janela_meses:])

    rede = historico.assign(_rede="rede")
    pontos = compute_monthly_share(rede, group_col="_rede", grupos=["rede"])

    candidatos = [ponto for ponto in pontos if ponto["competencia"] in competencias_validas]
    candidatos.sort(key=lambda ponto: ponto["valor"])

    return [
        {"competencia": ponto["competencia"], "vinShareRede": ponto["valor"]}
        for ponto in candidatos[:limite]
    ]
