import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.main import app
from src.interfaces.api.routers import vin_share as vin_share_router

client = TestClient(app)


def _historico_pequeno() -> pd.DataFrame:
    hoje = pd.Timestamp.now().normalize()
    return pd.DataFrame([
        {
            "VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 100,
            "ServiceType": "Manutencao", "ServiceDate": hoje - pd.Timedelta(days=10),
            "SalesDate": hoje - pd.Timedelta(days=100), "DeliveryDate": hoje - pd.Timedelta(days=100),
        },
        {
            "VIN_Hash": "v2", "ModelName": "KA", "DealerCode": 200,
            "ServiceType": "Recall", "ServiceDate": hoje - pd.Timedelta(days=400),
            "SalesDate": hoje - pd.Timedelta(days=2000), "DeliveryDate": hoje - pd.Timedelta(days=2000),
        },
    ])


@pytest.fixture(autouse=True)
def _dados_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    # Evita depender do parquet real (600 mil linhas) e mantem os testes hermeticos.
    monkeypatch.setattr(vin_share_router, "load_vin_share_data", lambda: _historico_pequeno())


def test_vin_share_sem_filtros_retorna_200_com_schema_esperado() -> None:
    resposta = client.get("/api/vin-share")
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert corpo["totalVeiculosElegiveis"] == 2
    assert corpo["totalComServico"] == 2
    assert corpo["vinShareEstimado"] == 100.0
    assert corpo["filtrosAplicados"] == {
        "concessionaria": None, "modelo": None, "faixaIdade": None,
        "tipoServico": None, "periodoInicio": None, "periodoFim": None,
    }


def test_vin_share_filtro_modelo_restringe_resultado() -> None:
    resposta = client.get("/api/vin-share", params={"modelo": "RANGER"})
    corpo = resposta.json()

    assert corpo["totalVeiculosElegiveis"] == 1
    assert corpo["filtrosAplicados"]["modelo"] == "RANGER"


def test_vin_share_filtros_combinados() -> None:
    resposta = client.get(
        "/api/vin-share",
        params={"modelo": "KA", "tipoServico": "Recall", "concessionaria": "200"},
    )
    corpo = resposta.json()

    assert corpo["totalVeiculosElegiveis"] == 1
    assert corpo["totalComServico"] == 1
    assert corpo["filtrosAplicados"] == {
        "concessionaria": "200", "modelo": "KA", "faixaIdade": None,
        "tipoServico": "Recall", "periodoInicio": None, "periodoFim": None,
    }


def test_vin_share_faixa_idade_invalida_retorna_422() -> None:
    resposta = client.get("/api/vin-share", params={"faixaIdade": "9+"})
    assert resposta.status_code == 422


def test_vin_share_periodo_e_ecoado_em_formato_iso() -> None:
    resposta = client.get(
        "/api/vin-share",
        params={"periodoInicio": "2024-01-01", "periodoFim": "2024-12-31"},
    )
    corpo = resposta.json()

    assert corpo["filtrosAplicados"]["periodoInicio"] == "2024-01-01"
    assert corpo["filtrosAplicados"]["periodoFim"] == "2024-12-31"


def test_vin_share_periodo_invalido_retorna_422() -> None:
    resposta = client.get("/api/vin-share", params={"periodoInicio": "nao-e-uma-data"})
    assert resposta.status_code == 422


# --------------------------------------------------------------------------- #
# Robustez / casos de borda que nao devem derrubar o endpoint                  #
# --------------------------------------------------------------------------- #

def test_vin_share_faixa_idade_vazia_retorna_422() -> None:
    resposta = client.get("/api/vin-share", params={"faixaIdade": ""})
    assert resposta.status_code == 422


def test_vin_share_periodo_invertido_retorna_200_com_zero_resultados() -> None:
    resposta = client.get(
        "/api/vin-share",
        params={"periodoInicio": "2026-01-01", "periodoFim": "2020-01-01"},
    )
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert corpo["totalComServico"] == 0
    assert corpo["vinShareEstimado"] == 0.0


def test_vin_share_filtro_sem_correspondencia_retorna_200_com_zero_nao_erro() -> None:
    resposta = client.get(
        "/api/vin-share",
        params={"modelo": "MODELO_QUE_NAO_EXISTE", "concessionaria": "999999999"},
    )
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert corpo["totalVeiculosElegiveis"] == 0
    assert corpo["totalComServico"] == 0
    assert corpo["vinShareEstimado"] == 0.0


def test_vin_share_modelo_com_caracteres_especiais_nao_quebra() -> None:
    resposta = client.get(
        "/api/vin-share",
        params={"modelo": "RANGER'; DROP TABLE veiculos; -- <script>alert(1)</script> ção"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["totalVeiculosElegiveis"] == 0


def test_vin_share_query_param_desconhecido_e_ignorado() -> None:
    resposta = client.get("/api/vin-share", params={"paramInexistente": "qualquer-coisa"})
    assert resposta.status_code == 200


def test_vin_share_arquivo_de_dados_ausente_nao_derruba_o_processo() -> None:
    # Simula o cenario "esqueceram de rodar build_service_history": o handler propaga
    # a excecao, o middleware de erro do Starlette a converte em 500 — o processo da
    # API continua de pe para as proximas requisicoes, nao trava nem derruba o servidor.
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError(
            "Histórico de serviços não encontrado. Rode "
            "`python -m src.interfaces.pipeline.build_service_history`."
        )

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(vin_share_router, "load_vin_share_data", _sem_dados)
        resposta = client_sem_raise.get("/api/vin-share")

    assert resposta.status_code == 500

    # confirma que o processo segue saudavel para a proxima requisicao (dados restaurados
    # pelo fixture autouse fora deste bloco `with`)
    resposta_seguinte = client.get("/api/vin-share")
    assert resposta_seguinte.status_code == 200
