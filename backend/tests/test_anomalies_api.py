import pandas as pd
import pytest
from fastapi.testclient import TestClient
from tests.conftest import auth_headers

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


def test_anomalies_retorna_200_com_lista_bem_formada(monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    monkeypatch.setattr(anomalies_router, "load_vin_share_data", _historico_pequeno)

    resposta = client.get("/api/anomalies", headers=auth_headers(token_gestor))
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert isinstance(corpo, list)
    for item in corpo:
        assert set(item.keys()) == {"tipo", "entidade", "severidade", "descricao", "resumo", "valorReferencia", "valorAtual"}
        assert item["tipo"] in {"queda_dealer", "gap_modelo", "pico_mainsource"}
        assert 0.0 <= item["severidade"] <= 1.0


def test_anomalies_e_calculado_uma_unica_vez_e_fica_em_cache(monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    chamadas = {"n": 0}

    def _carregar_e_contar() -> pd.DataFrame:
        chamadas["n"] += 1
        return _historico_pequeno()

    monkeypatch.setattr(anomalies_router, "load_vin_share_data", _carregar_e_contar)

    client.get("/api/anomalies", headers=auth_headers(token_gestor))
    client.get("/api/anomalies", headers=auth_headers(token_gestor))
    client.get("/api/anomalies", headers=auth_headers(token_gestor))

    assert chamadas["n"] == 1


def test_anomalies_dataframe_vazio_nao_quebra(monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    monkeypatch.setattr(anomalies_router, "load_vin_share_data", _historico_vazio)

    resposta = client.get("/api/anomalies", headers=auth_headers(token_gestor))
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_anomalies_query_param_desconhecido_e_ignorado(monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    monkeypatch.setattr(anomalies_router, "load_vin_share_data", _historico_pequeno)

    resposta = client.get("/api/anomalies", params={"paramInexistente": "x"}, headers=auth_headers(token_gestor))
    assert resposta.status_code == 200


def test_anomalies_concessionaria_so_ve_o_proprio_dealer(
    monkeypatch: pytest.MonkeyPatch, token_concessionaria: str
) -> None:
    # gap_modelo (sem dealer) e' visivel; queda_dealer/pico_mainsource de outros
    # dealers, nao -- so' o 6693 (dealer do token_concessionaria).
    anomalias_calculadas = [
        {"tipo": "queda_dealer", "entidade": "6693", "severidade": 0.4, "descricao": "d1", "resumo": "r1", "valorReferencia": 1.0, "valorAtual": 2.0},
        {"tipo": "queda_dealer", "entidade": "9999", "severidade": 0.9, "descricao": "d2", "resumo": "r2", "valorReferencia": 1.0, "valorAtual": 2.0},
        {"tipo": "pico_mainsource", "entidade": "9999", "severidade": 0.5, "descricao": "d3", "resumo": "r3", "valorReferencia": 1.0, "valorAtual": 2.0},
        {"tipo": "gap_modelo", "entidade": "KA", "severidade": 0.3, "descricao": "d4", "resumo": "r4", "valorReferencia": 1.0, "valorAtual": 2.0},
    ]
    monkeypatch.setattr(anomalies_router, "_anomalias_calculadas", lambda: anomalias_calculadas)

    resposta = client.get("/api/anomalies", headers=auth_headers(token_concessionaria))
    corpo = resposta.json()

    assert resposta.status_code == 200
    tipos_e_entidades = {(item["tipo"], item["entidade"]) for item in corpo}
    assert tipos_e_entidades == {("queda_dealer", "6693"), ("gap_modelo", "KA")}


def test_anomalies_gestor_ve_anomalias_de_qualquer_dealer(
    monkeypatch: pytest.MonkeyPatch, token_gestor: str
) -> None:
    anomalias_calculadas = [
        {"tipo": "queda_dealer", "entidade": "6693", "severidade": 0.4, "descricao": "d1", "resumo": "r1", "valorReferencia": 1.0, "valorAtual": 2.0},
        {"tipo": "queda_dealer", "entidade": "9999", "severidade": 0.9, "descricao": "d2", "resumo": "r2", "valorReferencia": 1.0, "valorAtual": 2.0},
    ]
    monkeypatch.setattr(anomalies_router, "_anomalias_calculadas", lambda: anomalias_calculadas)

    resposta = client.get("/api/anomalies", headers=auth_headers(token_gestor))
    assert len(resposta.json()) == 2


def test_anomalies_arquivo_de_dados_ausente_nao_derruba_o_processo(token_gestor: str) -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError("Histórico de serviços não encontrado.")

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(anomalies_router, "load_vin_share_data", _sem_dados)
        resposta = client_sem_raise.get("/api/anomalies", headers=auth_headers(token_gestor))

    assert resposta.status_code == 500

    anomalies_router._anomalias_calculadas.cache_clear()
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(anomalies_router, "load_vin_share_data", _historico_pequeno)
        resposta_seguinte = client.get("/api/anomalies", headers=auth_headers(token_gestor))

    assert resposta_seguinte.status_code == 200
