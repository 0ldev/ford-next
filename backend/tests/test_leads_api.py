import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.main import app
from src.interfaces.api.routers import leads as leads_router
from src.interfaces.api.routers.leads import LIMIT_PADRAO

client = TestClient(app)


def _leads_teste() -> pd.DataFrame:
    linhas = [
        {"vin": "v1", "dealerCode": "100", "score": 0.9, "motivo": "motivo v1", "modelo": "RANGER"},
        {"vin": "v2", "dealerCode": "100", "score": 0.3, "motivo": "motivo v2", "modelo": "KA"},
        {"vin": "v3", "dealerCode": "200", "score": 0.8, "motivo": "motivo v3", "modelo": "RANGER"},
        {"vin": "v4", "dealerCode": "200", "score": 0.1, "motivo": "motivo v4", "modelo": "ECOSPORT"},
    ]
    return pd.DataFrame(linhas)


def _features_teste() -> pd.DataFrame:
    linhas = [
        {"VIN_Hash": "v1", "dias_desde_ultimo_servico": 400.0},
        {"VIN_Hash": "v2", "dias_desde_ultimo_servico": 90.0},
        {"VIN_Hash": "v3", "dias_desde_ultimo_servico": 250.0},
        {"VIN_Hash": "v4", "dias_desde_ultimo_servico": 10.0},
    ]
    return pd.DataFrame(linhas)


@pytest.fixture(autouse=True)
def _dados_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: _leads_teste())
    monkeypatch.setattr(leads_router, "load_features", lambda: _features_teste())


def test_leads_sem_filtro_retorna_todos_ordenados_por_score_desc() -> None:
    resposta = client.get("/api/leads")
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert [linha["vin"] for linha in corpo] == ["v1", "v3", "v2", "v4"]
    assert [linha["score"] for linha in corpo] == sorted((linha["score"] for linha in corpo), reverse=True)


def test_leads_devolve_vin_score_motivo_e_concessionaria() -> None:
    resposta = client.get("/api/leads")
    primeiro = resposta.json()[0]

    assert set(primeiro.keys()) == {"vin", "dealerCode", "score", "motivo", "modelo"}
    assert primeiro == {
        "vin": "v1", "dealerCode": "100", "score": 0.9, "motivo": "motivo v1", "modelo": "RANGER",
    }


def test_leads_filtro_concessionaria_restringe_e_mantem_ordem() -> None:
    resposta = client.get("/api/leads", params={"concessionaria": "200"})
    corpo = resposta.json()

    assert [linha["vin"] for linha in corpo] == ["v3", "v4"]
    assert all(linha["dealerCode"] == "200" for linha in corpo)


def test_leads_concessionaria_sem_correspondencia_retorna_lista_vazia() -> None:
    resposta = client.get("/api/leads", params={"concessionaria": "999999"})
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_leads_respeita_o_limite_top_50(monkeypatch: pytest.MonkeyPatch) -> None:
    muitos_leads = pd.DataFrame([
        {"vin": f"v{i}", "dealerCode": "100", "score": i / 1000, "motivo": "m", "modelo": "RANGER"}
        for i in range(200)
    ])
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: muitos_leads)

    resposta = client.get("/api/leads")
    corpo = resposta.json()

    assert len(corpo) == LIMIT_PADRAO
    assert corpo[0]["vin"] == "v199"  # maior score
    assert corpo[-1]["vin"] == "v150"  # 50-esimo maior


def test_leads_query_param_desconhecido_e_ignorado() -> None:
    resposta = client.get("/api/leads", params={"paramInexistente": "qualquer-coisa"})
    assert resposta.status_code == 200


def test_leads_arquivo_de_dados_ausente_nao_derruba_o_processo() -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError(
            "Lista de leads não encontrada. Rode `python -m src.interfaces.pipeline.generate_leads`."
        )

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(leads_router, "load_leads_data", _sem_dados)
        resposta = client_sem_raise.get("/api/leads")

    assert resposta.status_code == 500

    resposta_seguinte = client.get("/api/leads")
    assert resposta_seguinte.status_code == 200


# --------------------------------------------------------------------------- #
# GET /api/leads/{vin}/acao                                                    #
# --------------------------------------------------------------------------- #

def test_acao_recomendada_score_alto_e_contato_ativo() -> None:
    resposta = client.get("/api/leads/v1/acao")  # score 0.9, 400 dias sem servico
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert corpo["acao"] == "contato_ativo"
    assert "RANGER" in corpo["mensagem"]
    assert "400 dias" in corpo["mensagem"]


def test_acao_recomendada_score_medio_e_oferta() -> None:
    resposta = client.get("/api/leads/v2/acao")  # score 0.3, 90 dias sem servico
    corpo = resposta.json()

    assert corpo["acao"] == "oferta"
    assert "KA" in corpo["mensagem"]
    assert "90 dias" in corpo["mensagem"]


def test_acao_recomendada_score_baixo_e_lembrete() -> None:
    resposta = client.get("/api/leads/v4/acao")  # score 0.1, 10 dias sem servico
    corpo = resposta.json()

    assert corpo["acao"] == "lembrete"
    assert "ECOSPORT" in corpo["mensagem"]
    assert "10 dias" in corpo["mensagem"]


def test_acao_recomendada_vin_sem_features_usa_dias_zero_sem_quebrar(monkeypatch: pytest.MonkeyPatch) -> None:
    # VIN presente em leads.csv mas ausente de vehicle_features.parquet (nao deveria
    # acontecer nos dados reais, mas o endpoint nao pode quebrar se acontecer).
    monkeypatch.setattr(leads_router, "load_features", lambda: _features_teste().iloc[0:0])

    resposta = client.get("/api/leads/v1/acao")
    assert resposta.status_code == 200
    assert "0 dias" in resposta.json()["mensagem"]


def test_acao_recomendada_devolve_exatamente_acao_e_mensagem() -> None:
    resposta = client.get("/api/leads/v3/acao")
    assert set(resposta.json().keys()) == {"acao", "mensagem"}


def test_acao_recomendada_vin_inexistente_retorna_404() -> None:
    resposta = client.get("/api/leads/vin-que-nao-existe/acao")
    assert resposta.status_code == 404
    assert "vin-que-nao-existe" in resposta.json()["detail"]


def test_acao_recomendada_arquivo_de_dados_ausente_nao_derruba_o_processo() -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError("Lista de leads não encontrada.")

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(leads_router, "load_leads_data", _sem_dados)
        resposta = client_sem_raise.get("/api/leads/v1/acao")

    assert resposta.status_code == 500

    resposta_seguinte = client.get("/api/leads/v1/acao")
    assert resposta_seguinte.status_code == 200
