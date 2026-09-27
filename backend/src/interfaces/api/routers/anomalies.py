"""Router do endpoint GET /api/anomalies (schema combinado com o Paulo, front-end).

Schema de resposta — mesmo contrato de `frontend/src/domain/types.ts::AnomaliesResponse`
(lista, sem envelope; sem query params — o painel do front-end busca sempre tudo):

    [
      {
        "tipo": "queda_dealer",
        "entidade": "2185",
        "severidade": 0.34,
        "descricao": "Queda de 34% no VIN Share nos últimos 3 meses (3.6% para 2.4%).",
        "resumo": "Queda de 34% no VIN Share nos últimos 3 meses",
        "valorReferencia": 3.6,
        "valorAtual": 2.4
      },
      {
        "tipo": "gap_modelo",
        "entidade": "KA",
        "severidade": 0.21,
        "descricao": "0.3% de VIN Share, 6.3 pontos abaixo da média da rede (6.7%). Frota de 50.374 veículos.",
        "resumo": "VIN Share 6.3 pontos abaixo da média da rede (frota de 50.374 veículos)",
        "valorReferencia": 6.7,
        "valorAtual": 0.3
      },
      {
        "tipo": "pico_mainsource",
        "entidade": "3127",
        "severidade": 0.58,
        "descricao": "Aumento de 11.5 pontos na proporção de serviços fora do agendamento oficial (11.7% para 23.2% das ordens).",
        "resumo": "Aumento de 11.5 pontos na proporção de serviços fora do agendamento oficial",
        "valorReferencia": 11.7,
        "valorAtual": 23.2
      },
      ...
    ]

`tipo` é um de `"queda_dealer" | "gap_modelo" | "pico_mainsource"`. `entidade` é o
`DealerCode` (texto) para `queda_dealer`/`pico_mainsource`, ou o `ModelName` para
`gap_modelo` — este dataset não tem uma tabela de nomes de concessionária, só o
código. `severidade` é 0–1. `descricao` é a frase completa (mantida por
compatibilidade/acessibilidade); `resumo` é a mesma ideia sem o parêntese de
valores, para o front-end compor um cartão mais visual com `valorReferencia` ->
`valorAtual` como uma linha separada (ambos em %, mesma escala nos três tipos —
para `gap_modelo`, `valorReferencia` é a média da rede e `valorAtual` o valor do
modelo, não um "antes" temporal). Ver `application.anomaly_detection` para os
limiares e janelas usados em cada tipo (heurísticas documentadas, não uma
calibração completa) — e a ressalva sobre `pico_mainsource` não distinguir "saiu
da rede Ford" de "atendido sem passar pelo agendamento oficial" (só o segundo é
observável neste dataset).

O cálculo é custoso (~3-4s sobre o histórico completo) e não depende de nenhum
parâmetro de request — fica em cache (`lru_cache`) após a primeira chamada, aquecido
no startup da API (ver `main.py`).
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.application.anomaly_detection import compute_anomalies
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.dependencies import UsuarioAutenticado, obter_usuario_atual

router = APIRouter()


class Anomaly(BaseModel):
    tipo: str
    entidade: str
    severidade: float
    descricao: str
    resumo: str
    valorReferencia: float
    valorAtual: float


@lru_cache(maxsize=1)
def _anomalias_calculadas() -> list[dict]:
    return compute_anomalies(load_vin_share_data())


@router.get("/anomalies", response_model=list[Anomaly])
def get_anomalies(usuario: UsuarioAutenticado = Depends(obter_usuario_atual)) -> list[Anomaly]:
    return [Anomaly(**anomalia) for anomalia in _anomalias_calculadas()]
