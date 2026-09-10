"""Router do endpoint GET /api/leads (schema combinado com o Paulo, front-end).

Schema de resposta — mesmo contrato de `frontend/src/domain/types.ts::LeadsResponse`
(lista, sem envelope):

    [
      {
        "vin": "197ffa8b6cf53624205fe94e012b9c278b0fa6164a9c1a0a514ec9c41804364c",
        "dealerCode": "100",
        "score": 1.0,
        "motivo": "1016 dias sem servico, 306% acima do intervalo esperado do modelo",
        "modelo": "KA"
      },
      ...
    ]

Query params:
    - concessionaria (opcional): dealerCode. Ausente = fila da rede toda.

Paginação simples: sempre os `LIMIT_PADRAO` (50) leads de maior score dentro do
recorte de concessionária (se informado) — não há offset/cursor, a issue pede só
"top 50 por concessionária" como exemplo de paginação simples.

---

Router do endpoint GET /api/leads/{vin}/acao (schema combinado com o Paulo).

Schema de resposta — mesmo contrato de
`frontend/src/domain/types.ts::AcaoRecomendada`:

    {
      "acao": "contato_ativo",
      "mensagem": "Olá! Já faz 1016 dias desde a última manutenção do seu KA, bem
                   acima do intervalo recomendado. Um consultor da sua concessionária
                   Ford vai entrar em contato para ajudar a agendar sua revisão o
                   quanto antes."
    }

`acao` é um de `"lembrete" | "oferta" | "contato_ativo"`, calculado a partir do score
real do VIN em `leads.csv` (`domain.action_rules.recomendar_acao`); `mensagem` vem de
`domain.message_templates.montar_mensagem`, que também precisa de
`dias_desde_ultimo_servico` — não faz parte do schema de `leads.csv` (contrato
combinado com o Paulo), então é buscado em `vehicle_features.parquet` pelo VIN. 404 se
o VIN não estiver na lista de leads (não tem score pra basear a ação).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.domain.action_rules import Acao, recomendar_acao
from src.domain.message_templates import montar_mensagem
from src.infrastructure.leads_repository import load_leads_data
from src.interfaces.pipeline.build_features import load_features

router = APIRouter()

LIMIT_PADRAO = 50


class Lead(BaseModel):
    vin: str
    dealerCode: str
    score: float
    motivo: str
    modelo: str


class AcaoRecomendada(BaseModel):
    acao: Acao
    mensagem: str


@router.get("/leads", response_model=list[Lead])
def get_leads(
    concessionaria: str | None = Query(None, description="dealerCode; ausente traz a fila da rede toda"),
) -> list[Lead]:
    leads = load_leads_data()

    if concessionaria is not None:
        leads = leads[leads["dealerCode"] == concessionaria]

    leads = leads.sort_values("score", ascending=False).head(LIMIT_PADRAO)

    return [Lead(**linha) for linha in leads.to_dict(orient="records")]


@router.get("/leads/{vin}/acao", response_model=AcaoRecomendada)
def get_acao_recomendada(vin: str) -> AcaoRecomendada:
    leads = load_leads_data()
    linha = leads.loc[leads["vin"] == vin]

    if linha.empty:
        raise HTTPException(status_code=404, detail=f"VIN '{vin}' não encontrado na lista de leads.")

    score = float(linha["score"].iloc[0])
    modelo = str(linha["modelo"].iloc[0])

    features = load_features()
    linha_features = features.loc[features["VIN_Hash"] == vin]
    dias_sem_servico = (
        float(linha_features["dias_desde_ultimo_servico"].iloc[0]) if not linha_features.empty else 0.0
    )

    acao = recomendar_acao(score)
    mensagem = montar_mensagem(acao, modelo=modelo, dias_sem_servico=dias_sem_servico)

    return AcaoRecomendada(acao=acao, mensagem=mensagem)
