"""Router do endpoint GET /api/catalogo (schema combinado com o Paulo, front-end).

Schema de resposta:

    {
      "modelos": ["7BC", "BDA", ..., "RANGER", ...],
      "concessionarias": ["100", "104", ..., "1009", ...],
      "tiposServico": ["Maintenance"]
    }

Lista os valores distintos de `ModelName`, `DealerCode` e `ServiceType` do histórico de
serviços real — as opções verdadeiras para os dropdowns de filtro do dashboard
(`FiltrosBar`, `TrendChart`), em vez de uma lista fixa no frontend que ficaria
desatualizada se o catálogo do dataset mudar (gap identificado na revisão de
integração, issue #8).

Nota: `tiposServico` tem hoje um único valor real ("Maintenance") — o dataset não
distingue revisão programada de corretiva, garantia, recall etc. como o mock do
frontend supunha. O filtro de tipo de serviço continua funcional, só pouco
discriminante com os dados atuais.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.infrastructure.vin_share_repository import load_vin_share_data

router = APIRouter()


class CatalogoResponse(BaseModel):
    modelos: list[str]
    concessionarias: list[str]
    tiposServico: list[str]


@router.get("/catalogo", response_model=CatalogoResponse)
def get_catalogo() -> CatalogoResponse:
    df = load_vin_share_data()

    modelos = sorted(df["ModelName"].dropna().unique().tolist())
    # dropna antes de int: se a coluna tiver algum nulo em outro dataset, o pandas
    # promove o dtype pra float64 (int não representa NaN) — sem o dropna primeiro,
    # "100" viraria "100.0" no astype(str) direto.
    concessionarias = sorted(
        df["DealerCode"].dropna().astype(int).astype(str).unique().tolist(),
        key=lambda codigo: int(codigo) if codigo.isdigit() else codigo,
    )
    tipos_servico = sorted(df["ServiceType"].dropna().unique().tolist())

    return CatalogoResponse(modelos=modelos, concessionarias=concessionarias, tiposServico=tipos_servico)
