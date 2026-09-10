import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.main import app
from src.interfaces.api.routers import trend as trend_router

client = TestClient(app)


def _historico_pequeno() -> pd.DataFrame:
    linhas = [
        {"VIN_Hash": "v1", "ModelName": "RANGER", "ServiceDate": pd.Timestamp("2024-01-10")},
        {"VIN_Hash": "v2", "ModelName": "RANGER", "ServiceDate": pd.Timestamp("2024-01-15")},
        {"VIN_Hash": "v1", "ModelName": "RANGER", "ServiceDate": pd.Timestamp("2024-02-10")},
        {"VIN_Hash": "v3", "ModelName": "KA", "ServiceDate": pd.Timestamp("2024-01-05")},
    ]
    return pd.DataFrame(linhas)


@pytest.fixture(autouse=True)
def _dados_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trend_router, "load_vin_share_data", lambda: _historico_pequeno())


def test_trend_sem_filtro_retorna_todos_os_modelos() -> None:
    resposta = client.get("/api/trend", params={"periodoInicio": "2024-01", "periodoFim": "2024-02"})
    assert resposta.status_code == 200

    corpo = resposta.json()
    categorias = {ponto["categoria"] for ponto in corpo}
    assert categorias == {"RANGER", "KA"}
    assert all(set(ponto.keys()) == {"data", "valor", "categoria"} for ponto in corpo)


def test_trend_filtro_modelo_unico() -> None:
    resposta = client.get(
        "/api/trend",
        params={"modelo": "RANGER", "periodoInicio": "2024-01", "periodoFim": "2024-02"},
    )
    corpo = resposta.json()

    assert {ponto["categoria"] for ponto in corpo} == {"RANGER"}
    assert len(corpo) == 2  # 2 meses


def test_trend_filtro_modelo_repetido_aceita_multiplos_valores() -> None:
    resposta = client.get(
        "/api/trend",
        params=[("modelo", "RANGER"), ("modelo", "KA"), ("periodoInicio", "2024-01"), ("periodoFim", "2024-01")],
    )
    corpo = resposta.json()

    assert {ponto["categoria"] for ponto in corpo} == {"RANGER", "KA"}


def test_trend_valores_batem_com_vin_share_esperado() -> None:
    resposta = client.get(
        "/api/trend",
        params={"modelo": "RANGER", "periodoInicio": "2024-01", "periodoFim": "2024-02"},
    )
    corpo = {ponto["data"]: ponto["valor"] for ponto in resposta.json()}

    assert corpo["2024-01"] == 100.0  # v1 e v2, ambos com servico em jan
    assert corpo["2024-02"] == 50.0  # so v1 (v2 nao voltou)


def test_trend_sem_periodo_usa_intervalo_disponivel() -> None:
    resposta = client.get("/api/trend")
    competencias = {ponto["data"] for ponto in resposta.json()}

    assert competencias == {"2024-01", "2024-02"}


def test_trend_formato_de_periodo_invalido_retorna_422() -> None:
    resposta = client.get("/api/trend", params={"periodoInicio": "2024-01-01"})  # data completa, nao "YYYY-MM"
    assert resposta.status_code == 422


def test_trend_mes_invalido_retorna_422() -> None:
    resposta = client.get("/api/trend", params={"periodoInicio": "2024-13"})
    assert resposta.status_code == 422


def test_trend_periodo_invertido_retorna_200_com_lista_vazia() -> None:
    resposta = client.get("/api/trend", params={"periodoInicio": "2024-02", "periodoFim": "2024-01"})
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_trend_intervalo_absurdo_retorna_422_nao_trava() -> None:
    resposta = client.get("/api/trend", params={"periodoInicio": "1900-01", "periodoFim": "2200-01"})
    assert resposta.status_code == 422


def test_trend_modelo_inexistente_retorna_serie_de_zeros() -> None:
    resposta = client.get(
        "/api/trend",
        params={"modelo": "MODELO_INEXISTENTE", "periodoInicio": "2024-01", "periodoFim": "2024-01"},
    )
    corpo = resposta.json()

    assert len(corpo) == 1
    assert corpo[0]["valor"] == 0.0


def test_trend_query_param_desconhecido_e_ignorado() -> None:
    resposta = client.get("/api/trend", params={"paramInexistente": "x"})
    assert resposta.status_code == 200


def test_trend_arquivo_de_dados_ausente_nao_derruba_o_processo() -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError("Histórico de serviços não encontrado.")

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(trend_router, "load_vin_share_data", _sem_dados)
        resposta = client_sem_raise.get("/api/trend")

    assert resposta.status_code == 500

    resposta_seguinte = client.get("/api/trend")
    assert resposta_seguinte.status_code == 200
