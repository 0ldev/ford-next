import pandas as pd
import pytest
from fastapi.testclient import TestClient
from tests.conftest import auth_headers

from src.interfaces.api.main import app
from src.interfaces.api.routers import anomalies as anomalies_router
from src.interfaces.api.routers import leads as leads_router
from src.interfaces.api.routers import resumo as resumo_router

client = TestClient(app)


def _historico() -> pd.DataFrame:
    linhas = []
    # dealer 100: 4 VINs elegiveis, queda de jan/fev (100%) pra mar/abr (25%)
    for mes in ["2024-01", "2024-02"]:
        linhas += [
            {"VIN_Hash": f"v{i}", "ModelName": "RANGER", "DealerCode": 100, "ServiceDate": pd.Timestamp(f"{mes}-15"), "MainSource": "Agenda + Official Maintenance"}
            for i in range(4)
        ]
    for mes in ["2024-03", "2024-04"]:
        linhas.append({"VIN_Hash": "v0", "ModelName": "RANGER", "DealerCode": 100, "ServiceDate": pd.Timestamp(f"{mes}-15"), "MainSource": "Agenda + Official Maintenance"})
    return pd.DataFrame(linhas)


def _leads() -> pd.DataFrame:
    # 200 leads (piso padrao de amostra de modelos_maior_risco), 60% em risco alto.
    linhas = [
        {"vin": f"ka-alto-{i}", "dealerCode": "100", "score": 0.9, "motivo": "m", "modelo": "KA", "diasSemServico": 500.0}
        for i in range(120)
    ]
    linhas += [
        {"vin": f"ka-baixo-{i}", "dealerCode": "100", "score": 0.1, "motivo": "m", "modelo": "KA", "diasSemServico": 10.0}
        for i in range(80)
    ]
    return pd.DataFrame(linhas)


@pytest.fixture(autouse=True)
def _dados_de_teste(monkeypatch: pytest.MonkeyPatch):
    # `_anomalias_calculadas` e' cacheada (lru_cache) — precisa ser limpa entre
    # testes pra cada um usar seus proprios dados (mesmo motivo de test_anomalies_api).
    anomalies_router._anomalias_calculadas.cache_clear()
    monkeypatch.setattr(anomalies_router, "load_vin_share_data", lambda: _historico())
    monkeypatch.setattr(resumo_router, "load_vin_share_data", lambda: _historico())
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: _leads())
    monkeypatch.setattr(resumo_router, "load_leads_data", lambda: _leads())
    yield
    anomalies_router._anomalias_calculadas.cache_clear()


def test_resumo_executivo_retorna_as_tres_listas(token_gestor: str) -> None:
    resposta = client.get("/api/resumo-executivo", headers=auth_headers(token_gestor))
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert set(corpo.keys()) == {"concessionariasEmAlerta", "modelosMaiorRisco", "mesesMaiorChurn"}


def test_resumo_executivo_modelos_maior_risco_reflete_os_leads(token_gestor: str) -> None:
    resposta = client.get("/api/resumo-executivo", headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert corpo["modelosMaiorRisco"][0] == {"modelo": "KA", "percentualAltoRisco": 60.0, "totalVeiculos": 200}


def test_resumo_executivo_concessionaria_so_ve_a_propria_concessionaria_em_alerta(
    monkeypatch: pytest.MonkeyPatch, token_concessionaria: str
) -> None:
    anomalias_calculadas = [
        {"tipo": "queda_dealer", "entidade": "6693", "severidade": 0.4, "descricao": "d1", "resumo": "r1", "valorReferencia": 1.0, "valorAtual": 2.0},
        {"tipo": "pico_mainsource", "entidade": "9999", "severidade": 0.9, "descricao": "d2", "resumo": "r2", "valorReferencia": 1.0, "valorAtual": 2.0},
    ]
    monkeypatch.setattr(resumo_router, "_anomalias_calculadas", lambda: anomalias_calculadas)

    resposta = client.get("/api/resumo-executivo", headers=auth_headers(token_concessionaria))
    corpo = resposta.json()

    assert [item["dealerCode"] for item in corpo["concessionariasEmAlerta"]] == ["6693"]
    # agregados de rede continuam completos, sem escopo por dealer
    assert corpo["modelosMaiorRisco"][0]["modelo"] == "KA"


def test_resumo_executivo_arquivo_de_dados_ausente_nao_derruba_o_processo(token_gestor: str) -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError("Lista de leads não encontrada.")

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(resumo_router, "load_leads_data", _sem_dados)
        resposta = client_sem_raise.get("/api/resumo-executivo", headers=auth_headers(token_gestor))

    assert resposta.status_code == 500

    resposta_seguinte = client.get("/api/resumo-executivo", headers=auth_headers(token_gestor))
    assert resposta_seguinte.status_code == 200
