import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.main import app
from src.interfaces.api.routers import anomalies as anomalies_router

client = TestClient(app)


def _historico_pequeno() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 100,
            "ServiceDate": pd.Timestamp("2024-01-10"), "MainSource": "Agenda + Official Maintenance",
        },
    ])


def _historico_vazio() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": pd.array([], dtype="object"),
        "ModelName": pd.array([], dtype="object"),
        "DealerCode": pd.array([], dtype="int64"),
        "ServiceDate": pd.array([], dtype="datetime64[ns]"),
        "MainSource": pd.array([], dtype="object"),
    })


@pytest.fixture(autouse=True)
def _limpar_cache_de_anomalias() -> None:
    # `_anomalias_calculadas` e' cacheada (lru_cache) porque o endpoint nao tem
    # parametros — precisa ser limpa entre testes pra cada um usar seus proprios dados.
    anomalies_router._anomalias_calculadas.cache_clear()
    yield
    anomalies_router._anomalias_calculadas.cache_clear()


def test_anomalies_retorna_200_com_lista_bem_formada(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(anomalies_router, "load_vin_share_data", _historico_pequeno)

    resposta = client.get("/api/anomalies")
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert isinstance(corpo, list)
    for item in corpo:
        assert set(item.keys()) == {"tipo", "entidade", "severidade", "descricao"}
        assert item["tipo"] in {"queda_dealer", "gap_modelo", "pico_mainsource"}
        assert 0.0 <= item["severidade"] <= 1.0


def test_anomalies_e_calculado_uma_unica_vez_e_fica_em_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    chamadas = {"n": 0}

    def _carregar_e_contar() -> pd.DataFrame:
        chamadas["n"] += 1
        return _historico_pequeno()

    monkeypatch.setattr(anomalies_router, "load_vin_share_data", _carregar_e_contar)

    client.get("/api/anomalies")
    client.get("/api/anomalies")
    client.get("/api/anomalies")

    assert chamadas["n"] == 1


def test_anomalies_dataframe_vazio_nao_quebra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(anomalies_router, "load_vin_share_data", _historico_vazio)

    resposta = client.get("/api/anomalies")
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_anomalies_query_param_desconhecido_e_ignorado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(anomalies_router, "load_vin_share_data", _historico_pequeno)

    resposta = client.get("/api/anomalies", params={"paramInexistente": "x"})
    assert resposta.status_code == 200


def test_anomalies_arquivo_de_dados_ausente_nao_derruba_o_processo() -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError("Histórico de serviços não encontrado.")

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(anomalies_router, "load_vin_share_data", _sem_dados)
        resposta = client_sem_raise.get("/api/anomalies")

    assert resposta.status_code == 500

    anomalies_router._anomalias_calculadas.cache_clear()
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(anomalies_router, "load_vin_share_data", _historico_pequeno)
        resposta_seguinte = client.get("/api/anomalies")

    assert resposta_seguinte.status_code == 200
