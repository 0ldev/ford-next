import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.main import app
from src.interfaces.api.routers import catalogo as catalogo_router

client = TestClient(app)


def _historico_pequeno() -> pd.DataFrame:
    return pd.DataFrame([
        {"VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 100, "ServiceType": "Maintenance"},
        {"VIN_Hash": "v2", "ModelName": "KA", "DealerCode": 200, "ServiceType": "Maintenance"},
        {"VIN_Hash": "v3", "ModelName": "RANGER", "DealerCode": 100, "ServiceType": "Maintenance"},  # duplicatas nao devem repetir
        {"VIN_Hash": "v4", "ModelName": "ECOSPORT", "DealerCode": 1009, "ServiceType": "Recall"},
        {"VIN_Hash": "v5", "ModelName": None, "DealerCode": None, "ServiceType": None},  # nulos sao ignorados
    ])


@pytest.fixture(autouse=True)
def _dados_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(catalogo_router, "load_vin_share_data", lambda: _historico_pequeno())


def test_catalogo_retorna_200_com_schema_esperado() -> None:
    resposta = client.get("/api/catalogo")
    assert resposta.status_code == 200
    assert set(resposta.json().keys()) == {"modelos", "concessionarias", "tiposServico"}


def test_catalogo_lista_tipos_de_servico_distintos() -> None:
    corpo = client.get("/api/catalogo").json()
    assert corpo["tiposServico"] == ["Maintenance", "Recall"]


def test_catalogo_lista_modelos_distintos_em_ordem_alfabetica() -> None:
    corpo = client.get("/api/catalogo").json()
    assert corpo["modelos"] == ["ECOSPORT", "KA", "RANGER"]


def test_catalogo_lista_concessionarias_distintas_em_ordem_numerica() -> None:
    corpo = client.get("/api/catalogo").json()
    # ordem numerica (100, 200, 1009), nao lexicografica (1009, 100, 200)
    assert corpo["concessionarias"] == ["100", "200", "1009"]


def test_catalogo_ignora_valores_nulos() -> None:
    corpo = client.get("/api/catalogo").json()
    assert "None" not in corpo["modelos"]
    assert "None" not in corpo["concessionarias"]
    assert len(corpo["modelos"]) == 3
    assert len(corpo["concessionarias"]) == 3
