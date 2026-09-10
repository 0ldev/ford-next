"""Router do endpoint GET /api/trend (schema combinado com o Paulo, front-end).

Schema de resposta — mesmo contrato de `frontend/src/domain/types.ts::TrendResponse`
(lista, sem envelope; formato longo: uma linha por modelo/mês):

    [
      {"data": "2025-01", "valor": 11.2, "categoria": "RANGER"},
      {"data": "2025-02", "valor": 10.8, "categoria": "RANGER"},
      {"data": "2025-01", "valor": 9.4,  "categoria": "KA"},
      ...
    ]

Query params (mesmos nomes de `frontend/src/domain/types.ts::TrendFiltros`):
    - modelo (opcional, repetível: `?modelo=RANGER&modelo=KA`): ModelName. Ausente ou
      vazio = todos os modelos presentes no histórico.
    - periodoInicio / periodoFim (opcionais): competência "YYYY-MM" (não é data ISO
      completa — é mês, igual ao eixo do gráfico). Ausentes = intervalo integral
      disponível no histórico. Formato inválido → 422. Intervalo invertido → lista
      vazia (não erro). Intervalo maior que ~20 anos → 422 (proteção contra
      periodoInicio/periodoFim digitados errado).

`valor` é VIN share (%) — ver `application.trend_metrics.compute_monthly_share` para a
definição exata (elegível = todo VIN que já teve serviço daquele modelo, em toda a
história; "com serviço" = teve serviço naquele modelo especificamente naquele mês).
Meses sem serviço aparecem com `valor=0.0`, não ficam ausentes.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.application.trend_metrics import compute_trend
from src.infrastructure.vin_share_repository import load_vin_share_data

router = APIRouter()

_PADRAO_COMPETENCIA = r"^\d{4}-(0[1-9]|1[0-2])$"


class TrendPoint(BaseModel):
    data: str
    valor: float
    categoria: str


@router.get("/trend", response_model=list[TrendPoint])
def get_trend(
    modelo: Annotated[list[str] | None, Query(description="ModelName; repetível, ausente = todos")] = None,
    periodoInicio: Annotated[str | None, Query(pattern=_PADRAO_COMPETENCIA, description='Competência "YYYY-MM"')] = None,
    periodoFim: Annotated[str | None, Query(pattern=_PADRAO_COMPETENCIA, description='Competência "YYYY-MM"')] = None,
) -> list[TrendPoint]:
    df = load_vin_share_data()

    try:
        pontos = compute_trend(
            df,
            modelos=modelo or None,
            periodo_inicio=periodoInicio,
            periodo_fim=periodoFim,
        )
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro

    return [TrendPoint(**ponto) for ponto in pontos]
