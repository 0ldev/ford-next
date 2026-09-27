import pandas as pd
import pytest
from fastapi.testclient import TestClient
from tests.conftest import auth_headers

from src.interfaces.api.main import app
from src.interfaces.api.routers import catalogo as catalogo_router

client = TestClient(app)


def _historico_pequeno() -> pd.DataFrame:
    return pd.DataFrame([
        {"VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 100, "ServiceType": "Maintenance",
         "ServiceDate": pd.Timestamp("2021-03-10")},
        {"VIN_Hash": "v2", "ModelName": "KA", "DealerCode": 200, "ServiceType": "Maintenance",
         "ServiceDate": pd.Timestamp("2024-11-20")},
        {"VIN_Hash": "v3", "ModelName": "RANGER", "DealerCode": 100, "ServiceType": "Maintenance",  # duplicatas nao devem repetir
         "ServiceDate": pd.Timestamp("2022-06-01")},
        {"VIN_Hash": "v4", "ModelName": "ECOSPORT", "DealerCode": 1009, "ServiceType": "Recall",
         "ServiceDate": pd.NaT},  # data nula nao deve virar min/max
        {"VIN_Hash": "v5", "ModelName": None, "DealerCode": None, "ServiceType": None,
         "ServiceDate": None},  # nulos sao ignorados
    ])


@pytest.fixture(autouse=True)
def _dados_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(catalogo_router, "load_vin_share_data", lambda: _historico_pequeno())


def test_catalogo_retorna_200_com_schema_esperado(token_gestor: str) -> None:
    resposta = client.get("/api/catalogo", headers=auth_headers(token_gestor))
    assert resposta.status_code == 200
    assert set(resposta.json().keys()) == {
        "modelos", "concessionarias", "tiposServico", "periodoDisponivel",
    }


def test_catalogo_lista_tipos_de_servico_distintos(token_gestor: str) -> None:
    corpo = client.get("/api/catalogo", headers=auth_headers(token_gestor)).json()
    assert corpo["tiposServico"] == ["Maintenance", "Recall"]


def test_catalogo_lista_modelos_distintos_em_ordem_alfabetica(token_gestor: str) -> None:
    corpo = client.get("/api/catalogo", headers=auth_headers(token_gestor)).json()
    assert corpo["modelos"] == ["ECOSPORT", "KA", "RANGER"]


def test_catalogo_lista_concessionarias_distintas_em_ordem_numerica(token_gestor: str) -> None:
    corpo = client.get("/api/catalogo", headers=auth_headers(token_gestor)).json()
    # ordem numerica (100, 200, 1009), nao lexicografica (1009, 100, 200)
    assert corpo["concessionarias"] == ["100", "200", "1009"]


def test_catalogo_ignora_valores_nulos(token_gestor: str) -> None:
    corpo = client.get("/api/catalogo", headers=auth_headers(token_gestor)).json()
    assert "None" not in corpo["modelos"]
    assert "None" not in corpo["concessionarias"]
    assert len(corpo["modelos"]) == 3
    assert len(corpo["concessionarias"]) == 3


def test_catalogo_periodo_disponivel_e_o_intervalo_real_de_service_date(token_gestor: str) -> None:
    corpo = client.get("/api/catalogo", headers=auth_headers(token_gestor)).json()
    # v1=2021-03-10, v3=2022-06-01, v2=2024-11-20; v4 (NaT) e v5 (None) sao ignorados.
    assert corpo["periodoDisponivel"] == {"inicio": "2021-03-10", "fim": "2024-11-20"}


def test_catalogo_concessionaria_so_ve_o_proprio_dealer(token_concessionaria: str) -> None:
    # _historico_pequeno() tem os dealers 100/200/1009; token_concessionaria e' do 6693
    # (fora da lista) -- devolve vazio, nao inventa nem devolve os outros.
    corpo = client.get("/api/catalogo", headers=auth_headers(token_concessionaria)).json()
    assert corpo["concessionarias"] == []
    # modelos/tiposServico continuam completos, sem escopo por dealer
    assert corpo["modelos"] == ["ECOSPORT", "KA", "RANGER"]


def test_catalogo_concessionaria_ve_o_proprio_dealer_quando_presente(
    monkeypatch: pytest.MonkeyPatch, token_concessionaria: str
) -> None:
    historico_com_6693 = pd.DataFrame([
        {"VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 100, "ServiceType": "Maintenance", "ServiceDate": pd.Timestamp("2021-01-01")},
        {"VIN_Hash": "v2", "ModelName": "KA", "DealerCode": 6693, "ServiceType": "Maintenance", "ServiceDate": pd.Timestamp("2021-01-02")},
    ])
    monkeypatch.setattr(catalogo_router, "load_vin_share_data", lambda: historico_com_6693)

    corpo = client.get("/api/catalogo", headers=auth_headers(token_concessionaria)).json()
    assert corpo["concessionarias"] == ["6693"]


def test_catalogo_periodo_disponivel_e_null_sem_nenhuma_data_valida(
    monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    sem_datas = pd.DataFrame([
        {"VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 100, "ServiceType": "Maintenance",
         "ServiceDate": pd.NaT},
    ])
    monkeypatch.setattr(catalogo_router, "load_vin_share_data", lambda: sem_datas)

    corpo = client.get("/api/catalogo", headers=auth_headers(token_gestor)).json()
    assert corpo["periodoDisponivel"] is None
