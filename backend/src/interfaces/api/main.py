import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.infrastructure.leads_repository import load_leads_data
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.routers import anomalies, auth, catalogo, leads, resumo, trend, vin_share
from src.interfaces.api.routers.anomalies import _anomalias_calculadas

logger = logging.getLogger("ford_next")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Aquece os caches de repositorio/calculo no startup, nao na primeira requisicao —
    # sem isso o primeiro GET pagaria o custo de ler os arquivos processados (o de
    # vin-share tem ~600 mil linhas) ou, no caso de /api/anomalies, ~3-4s de deteccao.
    #
    # Cada aquecimento e' isolado (try/except por dataset): se UM estiver faltando, so
    # aquele endpoint fica indisponivel no primeiro GET (erro que os routers ja tratam
    # por requisicao) — nao derruba a API inteira na inicializacao, que e' exatamente o
    # que esse tratamento por requisicao foi desenhado para tolerar.
    for nome, carregar in (
        ("vin-share", load_vin_share_data),
        ("leads", load_leads_data),
        ("anomalies", _anomalias_calculadas),
    ):
        try:
            carregar()
        except FileNotFoundError as erro:
            print(f"[startup] aviso: nao foi possivel pre-carregar '{nome}': {erro}")
    yield


app = FastAPI(
    title="Ford Next API",
    version="1.0.0",
    description=(
        "VIN Share Intelligence Hub — VIN Share, tendência, anomalias e leads "
        "priorizados de risco de evasão da rede Ford. Autenticação via "
        "`POST /api/auth/login`; todo o resto exige `Authorization: Bearer <token>`."
    ),
    lifespan=lifespan,
)
app.include_router(auth.router, prefix="/api", tags=["Autenticação"])
app.include_router(vin_share.router, prefix="/api", tags=["VIN Share"])
app.include_router(leads.router, prefix="/api", tags=["Leads"])
app.include_router(trend.router, prefix="/api", tags=["Tendência"])
app.include_router(anomalies.router, prefix="/api", tags=["Anomalias"])
app.include_router(catalogo.router, prefix="/api", tags=["Catálogo"])
app.include_router(resumo.router, prefix="/api", tags=["Resumo executivo"])


# Códigos estáveis por faixa de status — pensados pra o front-end decidir
# comportamento (ex.: 401 -> forçar novo login) sem parsear a mensagem de `detail`.
_CODIGO_POR_STATUS: dict[int, str] = {
    400: "DADOS_INVALIDOS",
    401: "NAO_AUTENTICADO",
    403: "PROIBIDO",
    404: "NAO_ENCONTRADO",
    422: "DADOS_INVALIDOS",
}


@app.exception_handler(HTTPException)
async def tratar_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Mantém o contrato existente (`{"detail": ...}`) e acrescenta `codigo`.

    Não muda nada pra quem já consome `detail` (todo o front-end e os testes
    atuais) — só padroniza um campo extra, estável, pra quem quiser decidir
    comportamento sem parsear a mensagem.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "codigo": _CODIGO_POR_STATUS.get(exc.status_code, "ERRO")},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def tratar_erro_nao_tratado(request: Request, exc: Exception) -> JSONResponse:
    """Rede de segurança: qualquer exceção que escapou dos routers vira um 500 padronizado.

    Loga a exceção real no servidor (stack trace completo) mas nunca a
    devolve ao cliente — evita vazar detalhe interno (caminho de arquivo,
    tipo de exceção Python etc.) numa resposta de erro.
    """
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno no servidor.", "codigo": "ERRO_INTERNO"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
