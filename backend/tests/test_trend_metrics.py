import pandas as pd
import pytest

from src.application.trend_metrics import compute_monthly_share, compute_trend, listar_competencias


def _historico() -> pd.DataFrame:
    linhas = [
        # v1: RANGER, servico no dealer 100 em jan/2024 e no dealer 200 em fev/2024
        {"VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 100, "ServiceDate": pd.Timestamp("2024-01-15")},
        {"VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 200, "ServiceDate": pd.Timestamp("2024-02-10")},
        # v2: RANGER, servico no dealer 100 em jan/2024
        {"VIN_Hash": "v2", "ModelName": "RANGER", "DealerCode": 100, "ServiceDate": pd.Timestamp("2024-01-20")},
        # v3: KA, servico no dealer 200 em jan/2024
        {"VIN_Hash": "v3", "ModelName": "KA", "DealerCode": 200, "ServiceDate": pd.Timestamp("2024-01-05")},
    ]
    return pd.DataFrame(linhas)


def test_listar_competencias_intervalo_simples() -> None:
    assert listar_competencias("2024-01", "2024-04") == ["2024-01", "2024-02", "2024-03", "2024-04"]


def test_listar_competencias_invertido_retorna_lista_vazia() -> None:
    assert listar_competencias("2024-04", "2024-01") == []


def test_listar_competencias_acima_do_limite_levanta_value_error() -> None:
    with pytest.raises(ValueError):
        listar_competencias("2000-01", "2030-01")


def test_compute_monthly_share_dealer_conta_vin_em_cada_dealer_que_visitou() -> None:
    # v1 visitou os dealers 100 E 200 -> elegivel (denominador) nos dois, nao so no primeiro.
    resultado = compute_monthly_share(_historico(), group_col="DealerCode")
    por_dealer_mes = {(p["DealerCode"], p["competencia"]): p["valor"] for p in resultado}

    # dealer 100: elegiveis = v1, v2 (2); jan/2024 com servico: v1, v2 (2) -> 100%
    assert por_dealer_mes[(100, "2024-01")] == 100.0
    # dealer 100: fev/2024 nenhum servico -> 0%, sem buraco
    assert por_dealer_mes[(100, "2024-02")] == 0.0

    # dealer 200: elegiveis = v1, v3 (2); jan/2024 so v3 -> 50%
    assert por_dealer_mes[(200, "2024-01")] == 50.0
    # dealer 200: fev/2024 so v1 -> 50%
    assert por_dealer_mes[(200, "2024-02")] == 50.0


def test_compute_trend_agrupa_por_modelo_com_schema_do_front() -> None:
    resultado = compute_trend(_historico(), modelos=["RANGER"], periodo_inicio="2024-01", periodo_fim="2024-02")

    assert resultado == [
        {"data": "2024-01", "valor": 100.0, "categoria": "RANGER"},  # v1 e v2, ambos com servico em jan
        {"data": "2024-02", "valor": 50.0, "categoria": "RANGER"},  # so v1 (v2 nao voltou)
    ]


def test_compute_trend_sem_modelo_retorna_todos_em_ordem_alfabetica() -> None:
    resultado = compute_trend(_historico(), periodo_inicio="2024-01", periodo_fim="2024-01")
    categorias = [p["categoria"] for p in resultado]

    assert categorias == ["KA", "RANGER"]


def test_compute_trend_modelo_inexistente_retorna_serie_de_zeros_sem_erro() -> None:
    resultado = compute_trend(_historico(), modelos=["MODELO_INEXISTENTE"], periodo_inicio="2024-01", periodo_fim="2024-02")

    assert all(ponto["valor"] == 0.0 for ponto in resultado)
    assert len(resultado) == 2


def test_compute_trend_sem_periodo_usa_o_intervalo_disponivel_nos_dados() -> None:
    resultado = compute_trend(_historico())
    competencias = sorted({p["data"] for p in resultado})

    assert competencias == ["2024-01", "2024-02"]


def test_compute_monthly_share_dataframe_vazio_nao_quebra() -> None:
    vazio = _historico().iloc[0:0]
    resultado = compute_monthly_share(vazio, group_col="ModelName")

    assert resultado == []
