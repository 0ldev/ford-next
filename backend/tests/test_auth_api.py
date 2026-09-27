from fastapi.testclient import TestClient

from src.domain.security import decodificar_token
from src.interfaces.api.main import app

client = TestClient(app)


def test_login_com_credenciais_corretas_devolve_token_valido() -> None:
    resposta = client.post("/api/auth/login", json={"usuario": "gestor", "senha": "gestor123"})
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert set(corpo.keys()) == {"token", "perfil", "dealerCode", "expiraEm"}
    assert corpo["perfil"] == "gestor"
    assert corpo["dealerCode"] is None

    payload = decodificar_token(corpo["token"])
    assert payload.usuario == "gestor"
    assert payload.perfil == "gestor"


def test_login_de_concessionaria_devolve_o_proprio_dealer_code() -> None:
    resposta = client.post("/api/auth/login", json={"usuario": "concessionaria6693", "senha": "dealer123"})
    corpo = resposta.json()

    assert corpo["perfil"] == "concessionaria"
    assert corpo["dealerCode"] == "6693"


def test_login_senha_errada_retorna_401() -> None:
    resposta = client.post("/api/auth/login", json={"usuario": "gestor", "senha": "senha-errada"})
    assert resposta.status_code == 401
    assert "detail" in resposta.json()


def test_login_usuario_inexistente_retorna_401() -> None:
    resposta = client.post("/api/auth/login", json={"usuario": "nao-existe", "senha": "qualquer"})
    assert resposta.status_code == 401


def test_login_usuario_inexistente_e_senha_errada_devolvem_a_mesma_mensagem() -> None:
    # nao diferenciar "usuario nao existe" de "senha errada" evita revelar quais
    # usuarios existem so' pela mensagem de erro.
    resposta_usuario_invalido = client.post("/api/auth/login", json={"usuario": "nao-existe", "senha": "qualquer"})
    resposta_senha_invalida = client.post("/api/auth/login", json={"usuario": "gestor", "senha": "errada"})

    assert resposta_usuario_invalido.json()["detail"] == resposta_senha_invalida.json()["detail"]


def test_login_sem_campo_obrigatorio_retorna_422() -> None:
    resposta = client.post("/api/auth/login", json={"usuario": "gestor"})
    assert resposta.status_code == 422


def test_endpoint_protegido_sem_token_retorna_401() -> None:
    resposta = client.get("/api/catalogo")
    assert resposta.status_code == 401


def test_endpoint_protegido_com_token_invalido_retorna_401() -> None:
    resposta = client.get("/api/catalogo", headers={"Authorization": "Bearer token-invalido"})
    assert resposta.status_code == 401


def test_health_continua_publico() -> None:
    assert client.get("/health").status_code == 200
