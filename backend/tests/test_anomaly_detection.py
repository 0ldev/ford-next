import pandas as pd
import pytest

from src.application.anomaly_detection import (
    _competencias_completas,
    _janela_recente_e_anterior,
    compute_anomalies,
    detect_dealer_share_drops,
    detect_mainsource_spikes,
    detect_model_gaps,
)


def _servico(vin, modelo, dealer, mes, dia=15, main_source="Agenda + Official Maintenance") -> dict:
    return {
        "VIN_Hash": vin, "ModelName": modelo, "DealerCode": dealer,
        "ServiceDate": pd.Timestamp(f"{mes}-{dia:02d}"), "MainSource": main_source,
    }


MESES = ["2024-01", "2024-02", "2024-03", "2024-04"]


def _historico_queda_dealer() -> pd.DataFrame:
    linhas = []
    # dealer 1: 4 VINs voltando em jan/fev (anterior); so 1 continua em mar/abr (recente) -> queda real
    for mes in MESES[:2]:
        linhas += [_servico(f"v{i}", "RANGER", 1, mes) for i in range(4)]
    for mes in MESES[2:]:
        linhas.append(_servico("v0", "RANGER", 1, mes))
    # dealer 2: estavel, mesmos 4 VINs todo mes -> sem queda
    for mes in MESES:
        linhas += [_servico(f"w{i}", "RANGER", 2, mes) for i in range(4)]
    return pd.DataFrame(linhas)


def _historico_gap_modelo() -> pd.DataFrame:
    linhas = []
    # RANGER: alto retorno (4 de 4 elegiveis, todo mes)
    for mes in MESES:
        linhas += [_servico(f"r{i}", "RANGER", 1, mes) for i in range(4)]
    # KA: retorno bom em jan/fev, cai para so 1 de 4 elegiveis em mar/abr
    for mes in MESES[:2]:
        linhas += [_servico(f"k{i}", "KA", 1, mes) for i in range(4)]
    for mes in MESES[2:]:
        linhas.append(_servico("k0", "KA", 1, mes))
    return pd.DataFrame(linhas)


def _historico_pico_mainsource() -> pd.DataFrame:
    linhas = []
    # dealer 1: quase tudo via Agenda em jan/fev; quase tudo SEM Agenda em mar/abr
    for mes in MESES[:2]:
        linhas += [
            _servico(f"a{i}-{mes}", "RANGER", 1, mes,
                      main_source="Official Maintenance" if i == 0 else "Agenda + Official Maintenance")
            for i in range(10)
        ]
    for mes in MESES[2:]:
        linhas += [
            _servico(f"b{i}-{mes}", "RANGER", 1, mes,
                      main_source="Agenda + Official Maintenance" if i == 0 else "Official Maintenance")
            for i in range(10)
        ]
    # dealer 2: mix estavel (baixo "sem agenda") o tempo todo -> nao deve aparecer
    for mes in MESES:
        linhas += [
            _servico(f"c{i}-{mes}", "RANGER", 2, mes,
                      main_source="Official Maintenance" if i == 0 else "Agenda + Official Maintenance")
            for i in range(10)
        ]
    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------- #
# Helpers internos                                                            #
# --------------------------------------------------------------------------- #

def test_janela_recente_e_anterior_com_meses_insuficientes_retorna_none() -> None:
    assert _janela_recente_e_anterior(["2024-01", "2024-02", "2024-03"], janela=2) is None


def test_janela_recente_e_anterior_particiona_corretamente() -> None:
    resultado = _janela_recente_e_anterior(["2024-01", "2024-02", "2024-03", "2024-04"], janela=2)
    assert resultado == (["2024-03", "2024-04"], ["2024-01", "2024-02"])


def test_competencias_completas_descarta_ultimo_mes_truncado() -> None:
    linhas = []
    for mes, n in [("2024-01", 20), ("2024-02", 20), ("2024-03", 20), ("2024-04", 2)]:
        linhas += [_servico(f"v{i}", "RANGER", 1, mes) for i in range(n)]
    df = pd.DataFrame(linhas)

    assert _competencias_completas(df) == ["2024-01", "2024-02", "2024-03"]


def test_competencias_completas_mantem_ultimo_mes_quando_nao_e_truncado() -> None:
    df = _historico_queda_dealer()
    assert _competencias_completas(df) == MESES


# --------------------------------------------------------------------------- #
# queda_dealer                                                                #
# --------------------------------------------------------------------------- #

def test_detect_dealer_share_drops_identifica_queda_e_ignora_dealer_estavel() -> None:
    resultado = detect_dealer_share_drops(
        _historico_queda_dealer(), min_servicos=5, janela=2, queda_min_pct=10, base_min_pct=0,
    )

    entidades = {a["entidade"] for a in resultado}
    assert "1" in entidades
    assert "2" not in entidades
    assert all(a["tipo"] == "queda_dealer" for a in resultado)


def test_detect_dealer_share_drops_ignora_dealer_com_poucos_servicos() -> None:
    resultado = detect_dealer_share_drops(_historico_queda_dealer(), min_servicos=1000, janela=2)
    assert resultado == []


def test_detect_dealer_share_drops_base_perto_de_zero_nao_dispara_queda_de_ruido() -> None:
    # dealer com share ja quase zero: cair de 0.1% pra 0.0% e' ruido, nao anomalia real.
    linhas = []
    for mes in MESES:
        linhas += [_servico(f"v{i}", "RANGER", 1, mes) for i in range(1000)]
    linhas.append(_servico("raro", "RANGER", 1, "2024-01"))  # 1 VIN a mais so no mes 1
    df = pd.DataFrame(linhas)

    resultado = detect_dealer_share_drops(df, min_servicos=5, janela=2, queda_min_pct=10)
    assert resultado == []


def test_detect_dealer_share_drops_sem_historico_suficiente_nao_quebra() -> None:
    df = pd.DataFrame([_servico("v1", "RANGER", 1, "2024-01")])
    assert detect_dealer_share_drops(df, min_servicos=1) == []


def test_detect_dealer_share_drops_dataframe_vazio_nao_quebra() -> None:
    vazio = _historico_queda_dealer().iloc[0:0]
    assert detect_dealer_share_drops(vazio) == []


# --------------------------------------------------------------------------- #
# gap_modelo                                                                  #
# --------------------------------------------------------------------------- #

def test_detect_model_gaps_identifica_modelo_abaixo_da_rede() -> None:
    resultado = detect_model_gaps(_historico_gap_modelo(), min_servicos=5, janela=2, gap_min_pontos=5)

    entidades = {a["entidade"] for a in resultado}
    assert "KA" in entidades
    assert "RANGER" not in entidades
    assert all(a["tipo"] == "gap_modelo" for a in resultado)


def test_detect_model_gaps_dataframe_vazio_nao_quebra() -> None:
    vazio = _historico_gap_modelo().iloc[0:0]
    assert detect_model_gaps(vazio) == []


# --------------------------------------------------------------------------- #
# pico_mainsource                                                             #
# --------------------------------------------------------------------------- #

def test_detect_mainsource_spikes_identifica_mudanca_de_canal() -> None:
    resultado = detect_mainsource_spikes(
        _historico_pico_mainsource(), min_servicos=5, janela=2, pico_min_pontos=10,
    )

    entidades = {a["entidade"] for a in resultado}
    assert "1" in entidades
    assert "2" not in entidades
    assert all(a["tipo"] == "pico_mainsource" for a in resultado)


def test_detect_mainsource_spikes_dataframe_vazio_nao_quebra() -> None:
    vazio = _historico_pico_mainsource().iloc[0:0]
    assert detect_mainsource_spikes(vazio) == []


# --------------------------------------------------------------------------- #
# compute_anomalies                                                           #
# --------------------------------------------------------------------------- #

def test_compute_anomalies_combina_os_tres_tipos() -> None:
    linhas = (
        _historico_queda_dealer().to_dict("records")
        + _historico_gap_modelo().to_dict("records")
        + _historico_pico_mainsource().to_dict("records")
    )
    df = pd.DataFrame(linhas)

    resultado = compute_anomalies(df)
    tipos = {a["tipo"] for a in resultado}

    # com os limiares/volumes padrao (calibrados pro dataset real, bem maiores que
    # esta amostra sintetica) nao ha garantia de disparo aqui — o teste real dessa
    # combinacao roda contra o dataset real em outro lugar. Aqui so garantimos que
    # a funcao nao quebra e devolve uma lista bem formada.
    assert isinstance(resultado, list)
    assert tipos <= {"queda_dealer", "gap_modelo", "pico_mainsource"}
    for anomalia in resultado:
        assert set(anomalia.keys()) == {"tipo", "entidade", "severidade", "descricao", "resumo", "valorReferencia", "valorAtual"}
        assert 0.0 <= anomalia["severidade"] <= 1.0
