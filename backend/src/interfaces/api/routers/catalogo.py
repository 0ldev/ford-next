"""Router do endpoint GET /api/catalogo (schema combinado com o Paulo, front-end).

Schema de resposta:

    {
      "modelos": ["7BC", "BDA", ..., "RANGER", ...],
      "concessionarias": ["100", "104", ..., "1009", ...],
      "tiposServico": ["Maintenance"],
      "periodoDisponivel": {"inicio": "2020-01-03", "fim": "2026-05-04"}
    }

`periodoDisponivel` é o intervalo de `ServiceDate` realmente presente no histórico —
usado pelo front-end para limitar os seletores de período (`min`/`max` dos campos de
data) a datas com dado de verdade, em vez de deixar o usuário escolher um recorte
vazio. `null` só no caso degenerado de não haver nenhuma `ServiceDate` válida.

Lista os valores distintos de `ModelName`, `DealerCode` e `ServiceType` do histórico de
serviços real — as opções verdadeiras para os dropdowns de filtro do dashboard
(`FiltrosBar`, `TrendChart`), em vez de uma lista fixa no frontend que ficaria
desatualizada se o catálogo do dataset mudar (gap identificado na revisão de
integração, issue #8).

Nota: `tiposServico` tem hoje um único valor real ("Maintenance") — o dataset não
distingue revisão programada de corretiva, garantia, recall etc. como o mock do
frontend supunha. O filtro de tipo de serviço continua funcional, só pouco
discriminante com os dados atuais.

Protegido: exige `Authorization: Bearer <token>`. Perfil `concessionaria` só vê o
próprio código em `concessionarias` — o seletor da tela já vem travado nesse
dealer, não faz sentido listar os outros 400+ (ver
`domain.authorization.filtrar_concessionarias_visiveis`); `modelos`/`tiposServico`/
`periodoDisponivel` continuam completos pros dois perfis.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.domain.authorization import filtrar_concessionarias_visiveis
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.dependencies import UsuarioAutenticado, obter_usuario_atual

router = APIRouter()


class PeriodoDisponivel(BaseModel):
    inicio: str
    fim: str


class CatalogoResponse(BaseModel):
    modelos: list[str]
    concessionarias: list[str]
    tiposServico: list[str]
    periodoDisponivel: PeriodoDisponivel | None


@router.get("/catalogo", response_model=CatalogoResponse)
def get_catalogo(usuario: UsuarioAutenticado = Depends(obter_usuario_atual)) -> CatalogoResponse:
    df = load_vin_share_data()

    modelos = sorted(df["ModelName"].dropna().unique().tolist())
    # dropna antes de int: se a coluna tiver algum nulo em outro dataset, o pandas
    # promove o dtype pra float64 (int não representa NaN) — sem o dropna primeiro,
    # "100" viraria "100.0" no astype(str) direto.
    concessionarias = sorted(
        df["DealerCode"].dropna().astype(int).astype(str).unique().tolist(),
        key=lambda codigo: int(codigo) if codigo.isdigit() else codigo,
    )
    concessionarias = filtrar_concessionarias_visiveis(usuario.perfil, usuario.dealer_code, concessionarias)
    tipos_servico = sorted(df["ServiceType"].dropna().unique().tolist())

    datas_validas = df["ServiceDate"].dropna()
    periodo_disponivel = (
        PeriodoDisponivel(
            inicio=datas_validas.min().strftime("%Y-%m-%d"),
            fim=datas_validas.max().strftime("%Y-%m-%d"),
        )
        if not datas_validas.empty
        else None
    )

    return CatalogoResponse(
        modelos=modelos,
        concessionarias=concessionarias,
        tiposServico=tipos_servico,
        periodoDisponivel=periodo_disponivel,
    )
