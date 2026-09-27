import pandas as pd

from src.application.resumo_executivo import (
    concessionarias_em_alerta,
    meses_maior_churn,
    modelos_maior_risco,
)


# --------------------------------------------------------------------------- #
# concessionarias_em_alerta                                                    #
# --------------------------------------------------------------------------- #

def _anomalia(tipo: str, entidade: str, severidade: float, resumo: str = "resumo qualquer") -> dict:
    return {"tipo": tipo, "entidade": entidade, "severidade": severidade, "resumo": resumo}


def test_concessionarias_em_alerta_ordena_por_severidade_desc() -> None:
    anomalias = [
        _anomalia("queda_dealer", "100", 0.3),
        _anomalia("pico_mainsource", "200", 0.8),
        _anomalia("queda_dealer", "300", 0.5),
    ]

    resultado = concessionarias_em_alerta(anomalias)

    assert [item["dealerCode"] for item in resultado] == ["200", "300", "100"]


def test_concessionarias_em_alerta_ignora_gap_modelo() -> None:
    # gap_modelo e' por modelo, nao por dealer -- nao faz sentido num resumo de
    # "concessionarias em alerta".
    anomalias = [_anomalia("gap_modelo", "KA", 0.9)]

    assert concessionarias_em_alerta(anomalias) == []


def test_concessionarias_em_alerta_mantem_so_o_pior_por_dealer() -> None:
    # dealer 100 aparece nos dois tipos -- so' o mais severo deve sobrar, sem
    # duplicar a mesma unidade no resumo.
    anomalias = [
        _anomalia("queda_dealer", "100", 0.4, "queda de VIN Share"),
        _anomalia("pico_mainsource", "100", 0.9, "pico de origem"),
    ]

    resultado = concessionarias_em_alerta(anomalias)

    assert len(resultado) == 1
    assert resultado[0]["severidade"] == 0.9
    assert resultado[0]["resumo"] == "pico de origem"


def test_concessionarias_em_alerta_respeita_o_limite() -> None:
    anomalias = [_anomalia("queda_dealer", str(i), i / 10) for i in range(10)]

    resultado = concessionarias_em_alerta(anomalias, limite=2)

    assert len(resultado) == 2
    assert [item["dealerCode"] for item in resultado] == ["9", "8"]


# --------------------------------------------------------------------------- #
# modelos_maior_risco                                                         #
# --------------------------------------------------------------------------- #

def _leads_por_modelo(modelo: str, n_alto: int, n_baixo: int) -> list[dict]:
    linhas = [
        {"vin": f"{modelo}-alto-{i}", "dealerCode": "100", "score": 0.9, "motivo": "m", "modelo": modelo, "diasSemServico": 500.0}
        for i in range(n_alto)
    ]
    linhas += [
        {"vin": f"{modelo}-baixo-{i}", "dealerCode": "100", "score": 0.1, "motivo": "m", "modelo": modelo, "diasSemServico": 10.0}
        for i in range(n_baixo)
    ]
    return linhas


def test_modelos_maior_risco_calcula_percentual_e_ordena_desc() -> None:
    leads = pd.DataFrame(
        _leads_por_modelo("KA", n_alto=80, n_baixo=20)  # 80% em risco alto
        + _leads_por_modelo("RANGER", n_alto=30, n_baixo=70)  # 30% em risco alto
    )

    resultado = modelos_maior_risco(leads, min_leads=50)

    assert [item["modelo"] for item in resultado] == ["KA", "RANGER"]
    assert resultado[0]["percentualAltoRisco"] == 80.0
    assert resultado[0]["totalVeiculos"] == 100
    assert resultado[1]["percentualAltoRisco"] == 30.0


def test_modelos_maior_risco_ignora_modelo_abaixo_do_piso_de_amostra() -> None:
    # ECOSPORT: 2 leads, 100% em risco alto -- puro ruido de amostra pequena, o
    # piso de min_leads e' o que evita essa unidade "vencer" o ranking a toa.
    leads = pd.DataFrame(
        _leads_por_modelo("KA", n_alto=10, n_baixo=90)  # 10%, mas 100 leads (acima do piso)
        + _leads_por_modelo("ECOSPORT", n_alto=2, n_baixo=0)  # 100%, mas so' 2 leads
    )

    resultado = modelos_maior_risco(leads, min_leads=50)

    assert [item["modelo"] for item in resultado] == ["KA"]


def test_modelos_maior_risco_sem_nenhum_modelo_elegivel_retorna_lista_vazia() -> None:
    leads = pd.DataFrame(_leads_por_modelo("KA", n_alto=1, n_baixo=1))

    assert modelos_maior_risco(leads, min_leads=50) == []


# --------------------------------------------------------------------------- #
# meses_maior_churn                                                            #
# --------------------------------------------------------------------------- #

def _servico(vin: str, mes: str, dia: int = 15) -> dict:
    return {"VIN_Hash": vin, "ServiceDate": pd.Timestamp(f"{mes}-{dia:02d}")}


def test_meses_maior_churn_ordena_pelo_menor_vin_share_primeiro() -> None:
    linhas = []
    # jan: 4 dos 4 VINs elegiveis com servico -> 100%
    for i in range(4):
        linhas.append(_servico(f"v{i}", "2024-01"))
    # fev: so' 1 dos 4 -> 25% (pior mes -- "maior churn")
    linhas.append(_servico("v0", "2024-02"))
    # mar: 2 dos 4 -> 50%
    linhas += [_servico("v0", "2024-03"), _servico("v1", "2024-03")]
    # abr: repete jan, so' pra nao truncar o ultimo mes (volume >= metade da media anterior)
    for i in range(4):
        linhas.append(_servico(f"v{i}", "2024-04"))

    historico = pd.DataFrame(linhas)
    resultado = meses_maior_churn(historico, limite=2)

    assert [item["competencia"] for item in resultado] == ["2024-02", "2024-03"]
    assert resultado[0]["vinShareRede"] == 25.0


def test_meses_maior_churn_descarta_o_ultimo_mes_se_truncado() -> None:
    linhas = []
    for mes in ["2024-01", "2024-02", "2024-03"]:
        linhas += [_servico(f"v{i}", mes) for i in range(20)]
    # abr: so' 2 ordens (mes truncado no snapshot) -- nao deveria aparecer no resumo
    # como se fosse o pior mes so' por estar incompleto.
    linhas += [_servico("v0", "2024-04"), _servico("v1", "2024-04")]

    historico = pd.DataFrame(linhas)
    resultado = meses_maior_churn(historico)

    assert "2024-04" not in {item["competencia"] for item in resultado}


def test_meses_maior_churn_ignora_meses_fora_da_janela_de_analise() -> None:
    # 2020-01 e 2024-01 tem o VIN share mais baixo de todos (20% e 80%,
    # respectivamente, entre eles 2020-01 e' o "pior" nominal) mas ficam fora da
    # janela de analise (janela_meses=4) — sem a janela, 2020-01 "venceria" o
    # ranking por ser o inicio da coleta de dado, nao por evasao real.
    linhas = [_servico("v-antigo", "2020-01")]
    for mes in ["2024-01", "2024-02", "2024-03", "2024-04"]:
        linhas += [_servico(f"v{i}", mes) for i in range(4)]
    linhas += [_servico("v0", "2024-05"), _servico("v1", "2024-05")]  # 2 de 5 -> 40%, pior DENTRO da janela

    historico = pd.DataFrame(linhas)
    resultado = meses_maior_churn(historico, limite=1, janela_meses=4)

    assert resultado[0]["competencia"] == "2024-05"
    assert resultado[0]["vinShareRede"] == 40.0


def test_meses_maior_churn_sem_nenhum_servico_retorna_lista_vazia() -> None:
    historico = pd.DataFrame({"VIN_Hash": pd.Series(dtype="object"), "ServiceDate": pd.Series(dtype="datetime64[ns]")})

    assert meses_maior_churn(historico) == []
