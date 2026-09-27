import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.main import app
from src.interfaces.api.routers import leads as leads_router
from tests.conftest import auth_headers

client = TestClient(app)


def _leads_teste() -> pd.DataFrame:
    linhas = [
        {"vin": "v1", "dealerCode": "6693", "score": 0.9, "motivo": "motivo v1", "modelo": "RANGER", "diasSemServico": 400.0, "prioridade": 0.9},
        {"vin": "v2", "dealerCode": "9999", "score": 0.3, "motivo": "motivo v2", "modelo": "KA", "diasSemServico": 90.0, "prioridade": 0.3},
    ]
    return pd.DataFrame(linhas)


@pytest.fixture(autouse=True)
def _dados_de_teste(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: _leads_teste())
    # Isola cada teste num CSV temporario -- nunca escreve no data/runtime/ real.
    monkeypatch.setattr("src.infrastructure.contatos_repository.CONTATOS_PATH", str(tmp_path / "contatos.csv"))


def test_registrar_contato_cria_e_devolve_o_registro(token_gestor: str) -> None:
    resposta = client.post(
        "/api/leads/v1/contatos", json={"acao": "contato_ativo"}, headers=auth_headers(token_gestor)
    )
    assert resposta.status_code == 201

    corpo = resposta.json()
    assert corpo["vin"] == "v1"
    assert corpo["acao"] == "contato_ativo"
    assert corpo["usuario"] == "gestor"
    assert "data" in corpo


def test_registrar_contato_depois_aparece_no_get(token_gestor: str) -> None:
    client.post("/api/leads/v1/contatos", json={"acao": "lembrete"}, headers=auth_headers(token_gestor))
    client.post("/api/leads/v1/contatos", json={"acao": "oferta"}, headers=auth_headers(token_gestor))

    resposta = client.get("/api/leads/v1/contatos", headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert [item["acao"] for item in corpo] == ["lembrete", "oferta"]


def test_get_contatos_de_vin_sem_nenhum_registro_retorna_lista_vazia(token_gestor: str) -> None:
    resposta = client.get("/api/leads/v1/contatos", headers=auth_headers(token_gestor))
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_registrar_contato_vin_inexistente_retorna_404(token_gestor: str) -> None:
    resposta = client.post(
        "/api/leads/vin-que-nao-existe/contatos", json={"acao": "oferta"}, headers=auth_headers(token_gestor)
    )
    assert resposta.status_code == 404


def test_get_contatos_vin_inexistente_retorna_404(token_gestor: str) -> None:
    resposta = client.get("/api/leads/vin-que-nao-existe/contatos", headers=auth_headers(token_gestor))
    assert resposta.status_code == 404


def test_concessionaria_registra_contato_no_proprio_dealer(token_concessionaria: str) -> None:
    # v1 e' do dealer 6693, o mesmo do token_concessionaria.
    resposta = client.post(
        "/api/leads/v1/contatos", json={"acao": "contato_ativo"}, headers=auth_headers(token_concessionaria)
    )
    assert resposta.status_code == 201


def test_concessionaria_nao_registra_contato_em_vin_de_outro_dealer(token_concessionaria: str) -> None:
    # v2 e' do dealer 9999, nao do 6693 do token.
    resposta = client.post(
        "/api/leads/v2/contatos", json={"acao": "contato_ativo"}, headers=auth_headers(token_concessionaria)
    )
    assert resposta.status_code == 403


def test_concessionaria_nao_le_contatos_de_vin_de_outro_dealer(token_concessionaria: str) -> None:
    resposta = client.get("/api/leads/v2/contatos", headers=auth_headers(token_concessionaria))
    assert resposta.status_code == 403


def test_registrar_contato_sem_token_retorna_401() -> None:
    resposta = client.post("/api/leads/v1/contatos", json={"acao": "oferta"})
    assert resposta.status_code == 401


def test_registrar_contato_com_acao_invalida_retorna_422(token_gestor: str) -> None:
    resposta = client.post(
        "/api/leads/v1/contatos", json={"acao": "acao-que-nao-existe"}, headers=auth_headers(token_gestor)
    )
    assert resposta.status_code == 422
