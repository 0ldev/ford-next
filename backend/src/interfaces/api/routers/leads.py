"""Router do endpoint GET /api/leads (schema combinado com o Paulo, front-end).

Schema de resposta — mesmo contrato de `frontend/src/domain/types.ts::LeadsResponse`
(lista, sem envelope):

    [
      {
        "vin": "197ffa8b6cf53624205fe94e012b9c278b0fa6164a9c1a0a514ec9c41804364c",
        "dealerCode": "100",
        "score": 1.0,
        "motivo": "1016 dias sem servico, 306% acima do intervalo esperado do modelo",
        "modelo": "KA",
        "diasSemServico": 1016.0,
        "prioridade": 0.91
      },
      ...
    ]

Query params:
    - concessionaria (opcional): dealerCode. Ausente = fila da rede toda.
    - scoreMinimo (opcional, 0-1): só leads com score >= esse piso.
    - scoreMaximo (opcional, 0-1): só leads com score < esse teto (banda exclusiva
      no limite superior). Sem isso, "risco médio" filtrado só com scoreMinimo=0.3
      continua trazendo os ~97 mil VINs empatados em score == 1.0 no topo — a
      banda "médio" só isola o meio de verdade (30% a 69%) com os dois limites
      juntos; "alto" (>=70%) não precisa de teto, é o topo aberto da distribuição.
      Filtram por `score` (risco puro), não por `prioridade` — a faixa de risco na
      tela é sobre o risco em si, não sobre a mistura com valor do cliente.
    - pagina (opcional, padrão 1) / tamanhoPagina (opcional, padrão 50, máx. 500):
      paginação de verdade sobre o recorte filtrado — não um `head()` fixo.
      `tamanhoPagina` dobra como "capacidade de contato": a página 1 já é, por
      construção, a lista dos N leads que mais compensa contatar esta semana.

Resposta: `{"leads": [...], "total": N, "pagina": P, "tamanhoPagina": T}`, onde
`total` é a contagem do recorte inteiro (após concessionaria/scoreMinimo, antes da
página) — é o que permite a tela mostrar "50 de 3214" e montar os botões de
anterior/próxima.

Ordenado por `prioridade` desc e, em empate, por `diasSemServico` desc — não por
`score` sozinho. `prioridade` (`domain.prioritization.compute_prioridade`) cruza
risco com valor do cliente (histórico de serviços) porque risco puro empata MUITO
(a heurística de baixo volume é binária — 0.0/1.0 — e o próprio modelo de ML satura
perto de 0/1 dado o AUC≈1.0 do baseline; ~97 mil dos 175 mil VINs têm `score == 1.0`
exatamente): sem um critério que enxergue além do score, a primeira página seria uma
fatia arbitrária desse empate gigante, e um veículo de risco alto mas sem histórico
de retorno furaria a fila na frente de um cliente fiel. O desempate por dias sem
serviço garante que, mesmo dentro de um empate de prioridade, o VIN genuinamente
mais atrasado apareça primeiro.

Todo endpoint deste router exige `Authorization: Bearer <token>`. Perfil
`concessionaria` é auto-escopado pro próprio `dealerCode` em `GET /leads` (e
recusado com 403 se pedir outro); em `GET /leads/{vin}/acao` e nos dois
endpoints de contato abaixo, o escopo é pelo `dealerCode` do próprio VIN (ver
`interfaces.api.dependencies`).

---

POST /api/leads/{vin}/contatos — registra que a concessionária entrou em
contato com aquele VIN (recurso real de escrita, persistido em
`data/runtime/contatos.csv` via `infrastructure.contatos_repository`):

    Request:  {"acao": "contato_ativo"}
    Response (201): {"vin": "...", "usuario": "concessionaria6693", "acao": "contato_ativo", "data": "2026-09-27T20:15:00+00:00"}

404 se o VIN não estiver em `leads.csv`; 403 se o VIN for de outro dealer (perfil
`concessionaria`). `usuario` vem do token, nunca do corpo da requisição — ninguém
registra contato em nome de outra pessoa.

GET /api/leads/{vin}/contatos — histórico de contatos daquele VIN, mais recente
por último (ordem de registro); lista vazia se nunca houve nenhum. Mesmas regras
de 404/403 do POST.

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
`domain.message_templates.montar_mensagem`, usando `diasSemServico` já presente em
`leads.csv`. 404 se o VIN não estiver na lista de leads (não tem score pra basear a
ação).

---

GET /api/leads/distribuicao-score — schema de resposta:

    [
      {"faixaInicio": 0.0, "faixaFim": 10.0, "quantidade": 15667},
      {"faixaInicio": 10.0, "faixaFim": 20.0, "quantidade": 892},
      ...
      {"faixaInicio": 90.0, "faixaFim": 100.0, "quantidade": 97490}
    ]

Sem query params — sempre a base inteira de `leads.csv` (~175 mil VINs), não o top 50
de `/leads`. Existe porque o top 50 não mostra a forma real da distribuição do score
(ver `application.leads_metrics.compute_score_distribution`: ela é fortemente
bimodal — a maior parte da frota está perto de 0% ou perto de 100%, quase nada no
meio, consequência direta de como o rótulo/score foi construído).
"""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.application.leads_metrics import compute_score_distribution
from src.domain.action_rules import Acao, recomendar_acao
from src.domain.message_templates import montar_mensagem
from src.infrastructure.contatos_repository import listar_contatos, registrar_contato
from src.infrastructure.leads_repository import load_leads_data
from src.interfaces.api.dependencies import (
    UsuarioAutenticado,
    escopar_concessionaria,
    obter_usuario_atual,
    verificar_dealer_do_recurso,
)

router = APIRouter()

LIMIT_PADRAO = 50
TAMANHO_PAGINA_MAXIMO = 500


class Lead(BaseModel):
    vin: str
    dealerCode: str
    score: float
    motivo: str
    modelo: str
    diasSemServico: float
    prioridade: float


class LeadsPagina(BaseModel):
    leads: list[Lead]
    total: int
    pagina: int
    tamanhoPagina: int


class AcaoRecomendada(BaseModel):
    acao: Acao
    mensagem: str


class FaixaScore(BaseModel):
    faixaInicio: float
    faixaFim: float
    quantidade: int


class ContatoRegistrado(BaseModel):
    vin: str
    usuario: str
    acao: Acao
    data: str


class RegistrarContatoRequest(BaseModel):
    acao: Acao


@router.get("/leads", response_model=LeadsPagina)
def get_leads(
    concessionaria: str | None = Query(None, description="dealerCode; ausente traz a fila da rede toda"),
    scoreMinimo: float | None = Query(None, ge=0.0, le=1.0, description="só leads com score >= esse piso"),
    scoreMaximo: float | None = Query(None, ge=0.0, le=1.0, description="só leads com score < esse teto"),
    pagina: int = Query(1, ge=1),
    tamanhoPagina: int = Query(LIMIT_PADRAO, ge=1, le=TAMANHO_PAGINA_MAXIMO),
    usuario: UsuarioAutenticado = Depends(obter_usuario_atual),
) -> LeadsPagina:
    # Perfil "concessionaria" nunca ve a fila da rede toda: sem filtro pedido, e'
    # auto-escopado pro proprio dealer; pedindo outro dealer, 403.
    concessionaria = escopar_concessionaria(usuario, concessionaria)

    leads = load_leads_data()

    if concessionaria is not None:
        leads = leads[leads["dealerCode"] == concessionaria]

    if scoreMinimo is not None:
        leads = leads[leads["score"] >= scoreMinimo]

    if scoreMaximo is not None:
        leads = leads[leads["score"] < scoreMaximo]

    leads = leads.sort_values(["prioridade", "diasSemServico"], ascending=[False, False])
    total = len(leads)

    inicio = (pagina - 1) * tamanhoPagina
    pagina_recortada = leads.iloc[inicio : inicio + tamanhoPagina]

    return LeadsPagina(
        leads=[Lead(**linha) for linha in pagina_recortada.to_dict(orient="records")],
        total=total,
        pagina=pagina,
        tamanhoPagina=tamanhoPagina,
    )


@router.get("/leads/distribuicao-score", response_model=list[FaixaScore])
def get_distribuicao_score(usuario: UsuarioAutenticado = Depends(obter_usuario_atual)) -> list[FaixaScore]:
    # Sem escopo por dealer de proposito: e' a forma da distribuicao da rede
    # inteira, nao ha uma leitura "por concessionaria" que faca sentido aqui.
    leads = load_leads_data()
    faixas = compute_score_distribution(leads)

    return [FaixaScore(**faixa) for faixa in faixas]


def _buscar_linha_do_lead(vin: str) -> pd.Series:
    leads = load_leads_data()
    linha = leads.loc[leads["vin"] == vin]

    if linha.empty:
        raise HTTPException(status_code=404, detail=f"VIN '{vin}' não encontrado na lista de leads.")

    return linha.iloc[0]


@router.get("/leads/{vin}/acao", response_model=AcaoRecomendada)
def get_acao_recomendada(vin: str, usuario: UsuarioAutenticado = Depends(obter_usuario_atual)) -> AcaoRecomendada:
    linha = _buscar_linha_do_lead(vin)
    verificar_dealer_do_recurso(usuario, str(linha["dealerCode"]))

    score = float(linha["score"])
    modelo = str(linha["modelo"])
    dias_sem_servico = float(linha["diasSemServico"])

    acao = recomendar_acao(score)
    mensagem = montar_mensagem(acao, modelo=modelo, dias_sem_servico=dias_sem_servico)

    return AcaoRecomendada(acao=acao, mensagem=mensagem)


@router.post("/leads/{vin}/contatos", response_model=ContatoRegistrado, status_code=201)
def registrar_contato_do_lead(
    vin: str,
    corpo: RegistrarContatoRequest,
    usuario: UsuarioAutenticado = Depends(obter_usuario_atual),
) -> ContatoRegistrado:
    """Registra que a concessionária entrou em contato com o VIN. 404 se o VIN não
    estiver na lista de leads; 403 se `usuario` (perfil concessionaria) não for do
    dealer do VIN. `usuario` do registro vem do token, nunca do corpo da requisição."""
    linha = _buscar_linha_do_lead(vin)
    verificar_dealer_do_recurso(usuario, str(linha["dealerCode"]))

    registro = registrar_contato(vin, usuario=usuario.usuario, acao=corpo.acao)

    return ContatoRegistrado(**registro.__dict__)


@router.get("/leads/{vin}/contatos", response_model=list[ContatoRegistrado])
def listar_contatos_do_lead(
    vin: str, usuario: UsuarioAutenticado = Depends(obter_usuario_atual)
) -> list[ContatoRegistrado]:
    linha = _buscar_linha_do_lead(vin)
    verificar_dealer_do_recurso(usuario, str(linha["dealerCode"]))

    return [ContatoRegistrado(**registro.__dict__) for registro in listar_contatos(vin)]
