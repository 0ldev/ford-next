from fastapi.testclient import TestClient

from src.interfaces.api.main import app


def test_health_returns_ok() -> None:
    # `with` é essencial aqui: só dentro do context manager o `lifespan` roda de
    # verdade. Sem ele, os testes passam mesmo que o startup esteja quebrado (foi
    # exatamente assim que a issue original passou pela revisão).
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_app_sobe_mesmo_se_um_dataset_de_aquecimento_estiver_faltando(monkeypatch) -> None:
    """Um dataset faltando no aquecimento do lifespan não pode derrubar a API inteira —
    cada endpoint já trata `FileNotFoundError` por requisição; o lifespan só faz um
    pré-carregamento best-effort."""

    def _quebra() -> None:
        raise FileNotFoundError("simulado para o teste")

    monkeypatch.setattr("src.interfaces.api.main.load_leads_data", _quebra)

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
