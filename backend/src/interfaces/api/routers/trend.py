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

---

GET /api/trend/concessionarias — mesmo schema e mesmas regras de período acima, só
que agrupado por `DealerCode` em vez de `ModelName` (`categoria` é o dealerCode,
texto). Query param `concessionaria` (repetível) no lugar de `modelo`; ausente = todas
as concessionárias do histórico com pelo menos `minVeiculos` VINs elegíveis (default
0 = sem piso) — o front-end é quem recorta pro top N num ranking (ver
`VinShareConcessionariaChart`). Sem esse piso, dealers de 1-2 VINs entopem o topo do
ranking em 100% (ou o fundo em 0%) por ruído estatístico, não por volume real — ver
`application.trend_metrics.compute_monthly_share` (`min_elegiveis`).
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.application.trend_metrics import compute_trend, compute_trend_concessionaria
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.dependencies import UsuarioAutenticado, escopar_concessionarias, obter_usuario_atual

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
    usuario: UsuarioAutenticado = Depends(obter_usuario_atual),
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


@router.get("/trend/concessionarias", response_model=list[TrendPoint])
def get_trend_concessionarias(
    concessionaria: Annotated[list[str] | None, Query(description="dealerCode; repetível, ausente = todas")] = None,
    periodoInicio: Annotated[str | None, Query(pattern=_PADRAO_COMPETENCIA, description='Competência "YYYY-MM"')] = None,
    periodoFim: Annotated[str | None, Query(pattern=_PADRAO_COMPETENCIA, description='Competência "YYYY-MM"')] = None,
    minVeiculos: Annotated[
        int, Query(ge=0, description="Piso de VINs elegíveis; ignorado se `concessionaria` for informado")
    ] = 0,
    usuario: UsuarioAutenticado = Depends(obter_usuario_atual),
) -> list[TrendPoint]:
    # Perfil "concessionaria" so' ve o proprio dealer, mesmo pedindo a lista toda.
    concessionaria = escopar_concessionarias(usuario, concessionaria)

    df = load_vin_share_data()

    try:
        pontos = compute_trend_concessionaria(
            df,
            concessionarias=concessionaria or None,
            periodo_inicio=periodoInicio,
            periodo_fim=periodoFim,
            min_veiculos=minVeiculos,
        )
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro

    return [TrendPoint(**ponto) for ponto in pontos]
