"""Router do endpoint GET /api/vin-share (schema combinado com o Paulo, front-end).

Schema de resposta — mesmo contrato de `frontend/src/domain/types.ts::VinShareResponse`:

    {
        "vinShareEstimado": 42.6,       // percentual (0-100) de veiculos elegiveis
                                        // que retornaram a rede sob os filtros
        "totalVeiculosElegiveis": 100066,
        "totalComServico": 42628,
        "filtrosAplicados": {           // eco dos filtros recebidos; null = nao aplicado
            "concessionaria": null,
            "modelo": "RANGER",
            "faixaIdade": null,
            "tipoServico": null,
            "periodoInicio": null,
            "periodoFim": null
        }
    }

Query params, todos opcionais e combinaveis (mesmos nomes de
`frontend/src/domain/types.ts::VinShareFiltros`):
    - concessionaria: DealerCode (comparado como texto)
    - modelo: ModelName (igualdade exata, ex. "RANGER")
    - faixaIdade: um de "0-1", "1-2", "2-4", "4+" (anos) — 422 se outro valor for enviado
    - tipoServico: ServiceType (igualdade exata)
    - periodoInicio / periodoFim: datas ISO "YYYY-MM-DD" (limites inclusivos)

Ver `application.vin_share_metrics.compute_vin_share` para a definicao exata de
"elegivel" vs. "com servico" (a semantica de `concessionaria` em particular).

Protegido: exige `Authorization: Bearer <token>` (ver `interfaces.api.routers.auth`).
Perfil `concessionaria` é auto-escopado pro próprio `dealerCode` — ver
`interfaces.api.dependencies.escopar_concessionaria`.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.application.vin_share_metrics import FaixaIdade, compute_vin_share
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.dependencies import UsuarioAutenticado, escopar_concessionaria, obter_usuario_atual

router = APIRouter()


class VinShareResponse(BaseModel):
    vinShareEstimado: float
    totalVeiculosElegiveis: int
    totalComServico: int
    filtrosAplicados: dict[str, str | None]


@router.get("/vin-share", response_model=VinShareResponse)
def get_vin_share(
    concessionaria: str | None = Query(None, description="DealerCode da concessionaria"),
    modelo: str | None = Query(None, description="ModelName, ex.: RANGER"),
    faixaIdade: FaixaIdade | None = Query(None, description="Faixa de idade do veiculo em anos"),
    tipoServico: str | None = Query(None, description="ServiceType"),
    periodoInicio: date | None = Query(None, description="Data ISO, limite inferior (inclusivo)"),
    periodoFim: date | None = Query(None, description="Data ISO, limite superior (inclusivo)"),
    usuario: UsuarioAutenticado = Depends(obter_usuario_atual),
) -> VinShareResponse:
    # Perfil "concessionaria" nunca ve a rede toda: sem filtro pedido, e' auto-
    # escopado pro proprio dealer; pedindo outro dealer, 403 (ver dependencies.py).
    concessionaria = escopar_concessionaria(usuario, concessionaria)

    df = load_vin_share_data()

    resultado = compute_vin_share(
        df,
        concessionaria=concessionaria,
        modelo=modelo,
        faixa_idade=faixaIdade,
        tipo_servico=tipoServico,
        periodo_inicio=pd.Timestamp(periodoInicio) if periodoInicio else None,
        periodo_fim=pd.Timestamp(periodoFim) if periodoFim else None,
    )

    return VinShareResponse(
        **resultado,
        filtrosAplicados={
            "concessionaria": concessionaria,
            "modelo": modelo,
            "faixaIdade": faixaIdade,
            "tipoServico": tipoServico,
            "periodoInicio": periodoInicio.isoformat() if periodoInicio else None,
            "periodoFim": periodoFim.isoformat() if periodoFim else None,
        },
    )
