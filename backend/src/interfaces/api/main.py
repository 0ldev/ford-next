from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.leads_repository import load_leads_data
from src.infrastructure.vin_share_repository import load_vin_share_data
from src.interfaces.api.routers import anomalies, leads, trend, vin_share
from src.interfaces.api.routers.anomalies import _anomalias_calculadas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Aquece os caches de repositorio/calculo no startup, nao na primeira requisicao —
    # sem isso o primeiro GET pagaria o custo de ler os arquivos processados (o de
    # vin-share tem ~600 mil linhas) ou, no caso de /api/anomalies, ~3-4s de deteccao.
    load_vin_share_data()
    load_leads_data()
    _anomalias_calculadas()
    yield


app = FastAPI(title="Ford Next API", lifespan=lifespan)
app.include_router(vin_share.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(trend.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
