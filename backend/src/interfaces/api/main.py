from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.leads_repository import load_leads_data
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.routers import anomalies, catalogo, leads, resumo, trend, vin_share
from src.interfaces.api.routers.anomalies import _anomalias_calculadas


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


app = FastAPI(title="Ford Next API", lifespan=lifespan)
app.include_router(vin_share.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(trend.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(catalogo.router, prefix="/api")
app.include_router(resumo.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
