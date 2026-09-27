"""Router do endpoint GET /api/resumo-executivo.

Schema de resposta — mesmo contrato de `frontend/src/domain/types.ts::ResumoExecutivo`:

    {
      "concessionariasEmAlerta": [
        {"dealerCode": "3127", "tipo": "pico_mainsource", "severidade": 0.58,
         "resumo": "Aumento de 11.5 pontos na proporção de serviços fora do agendamento oficial"},
        ...
      ],
      "modelosMaiorRisco": [
        {"modelo": "KA", "percentualAltoRisco": 62.3, "totalVeiculos": 50374},
        ...
      ],
      "mesesMaiorChurn": [
        {"competencia": "2025-03", "vinShareRede": 8.4},
        ...
      ]
    }

Sem query params: é sempre o recorte de rede inteira, top 3 por lista — a versão
"bateu o olho" do dashboard, não mais um filtro. Ver `application.resumo_executivo`
para a lógica de cada lista; reaproveita `_anomalias_calculadas` (já em cache) para
as concessionárias em alerta, então não recalcula anomalias aqui.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.application.resumo_executivo import (
    concessionarias_em_alerta,
    meses_maior_churn,
    modelos_maior_risco,
)
from src.infrastructure.leads_repository import load_leads_data
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.routers.anomalies import _anomalias_calculadas

router = APIRouter()


class ConcessionariaEmAlerta(BaseModel):
    dealerCode: str
    tipo: str
    severidade: float
    resumo: str


class ModeloMaiorRisco(BaseModel):
    modelo: str
    percentualAltoRisco: float
    totalVeiculos: int


class MesMaiorChurn(BaseModel):
    competencia: str
    vinShareRede: float


class ResumoExecutivo(BaseModel):
    concessionariasEmAlerta: list[ConcessionariaEmAlerta]
    modelosMaiorRisco: list[ModeloMaiorRisco]
    mesesMaiorChurn: list[MesMaiorChurn]


@router.get("/resumo-executivo", response_model=ResumoExecutivo)
def get_resumo_executivo() -> ResumoExecutivo:
    return ResumoExecutivo(
        concessionariasEmAlerta=[
            ConcessionariaEmAlerta(**item) for item in concessionarias_em_alerta(_anomalias_calculadas())
        ],
        modelosMaiorRisco=[ModeloMaiorRisco(**item) for item in modelos_maior_risco(load_leads_data())],
        mesesMaiorChurn=[MesMaiorChurn(**item) for item in meses_maior_churn(load_vin_share_data())],
    )
