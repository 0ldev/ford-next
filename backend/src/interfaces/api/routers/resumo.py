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

Protegido: exige `Authorization: Bearer <token>`. Perfil `concessionaria` só vê a
própria concessionária em `concessionariasEmAlerta` (mesma regra de `GET
/api/anomalies` — ver `domain.authorization.filtrar_anomalias_por_perfil`);
`modelosMaiorRisco`/`mesesMaiorChurn` são agregados de rede sem dimensão de
dealer e continuam completos pros dois perfis.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.application.resumo_executivo import (
    concessionarias_em_alerta,
    meses_maior_churn,
    modelos_maior_risco,
)
from src.domain.authorization import filtrar_anomalias_por_perfil
from src.infrastructure.leads_repository import load_leads_data
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.dependencies import UsuarioAutenticado, obter_usuario_atual
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
def get_resumo_executivo(usuario: UsuarioAutenticado = Depends(obter_usuario_atual)) -> ResumoExecutivo:
    anomalias = filtrar_anomalias_por_perfil(usuario.perfil, usuario.dealer_code, _anomalias_calculadas())

    return ResumoExecutivo(
        concessionariasEmAlerta=[
            ConcessionariaEmAlerta(**item) for item in concessionarias_em_alerta(anomalias)
        ],
        modelosMaiorRisco=[ModeloMaiorRisco(**item) for item in modelos_maior_risco(load_leads_data())],
        mesesMaiorChurn=[MesMaiorChurn(**item) for item in meses_maior_churn(load_vin_share_data())],
    )
