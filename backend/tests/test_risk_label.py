import pandas as pd
import pytest

from src.domain.risk_label import (
    GAP_RELATIVO_THRESHOLD,
    add_em_risco,
    compute_em_risco,
    compute_gap_com_fallback,
)


def test_acima_do_threshold_e_em_risco() -> None:
    gap = pd.Series([GAP_RELATIVO_THRESHOLD + 0.5])
    assert compute_em_risco(gap).iloc[0] == True  # noqa: E712


def test_exatamente_no_threshold_nao_e_em_risco() -> None:
    gap = pd.Series([GAP_RELATIVO_THRESHOLD])
    assert compute_em_risco(gap).iloc[0] == False  # noqa: E712 (> estrito, nao >=)


def test_abaixo_do_threshold_nao_e_em_risco() -> None:
    gap = pd.Series([0.5])
    assert compute_em_risco(gap).iloc[0] == False  # noqa: E712


def test_gap_relativo_nulo_gera_na_nao_false() -> None:
    gap = pd.Series([None])
    assert compute_em_risco(gap).iloc[0] is pd.NA


def test_threshold_e_parametrizavel() -> None:
    gap = pd.Series([1.2])
    assert compute_em_risco(gap, threshold=1.0).iloc[0] == True  # noqa: E712
    assert compute_em_risco(gap, threshold=1.5).iloc[0] == False  # noqa: E712


def test_add_em_risco_adiciona_coluna_sem_modificar_original() -> None:
    acima = GAP_RELATIVO_THRESHOLD + 0.5
    abaixo = GAP_RELATIVO_THRESHOLD - 0.5
    df = pd.DataFrame({"VIN_Hash": ["a", "b", "c"], "gap_relativo": [acima, abaixo, None]})
    original = df.copy()

    resultado = add_em_risco(df)

    assert resultado["em_risco"].tolist() == [True, False, pd.NA]
    pd.testing.assert_frame_equal(df, original)


def test_add_em_risco_respeita_threshold_customizado() -> None:
    df = pd.DataFrame({"gap_relativo": [1.2]})
    resultado = add_em_risco(df, threshold=1.0)
    assert resultado["em_risco"].iloc[0] == True  # noqa: E712


def _entrada_fallback() -> dict[str, pd.Series]:
    return {
        "gap_relativo": pd.Series([2.0, None, None, 5.0]),
        "idade_dias": pd.Series([1000.0, 300.0, 100.0, 400.0]),
        "intervalo_mediano_esperado": pd.Series([100.0, 150.0, None, 200.0]),
        "n_servicos": pd.Series([3, 1, 1, 1]),
    }


def test_usa_gap_relativo_quando_vin_tem_gap_historico_proprio() -> None:
    entrada = _entrada_fallback()
    resultado = compute_gap_com_fallback(**entrada)
    assert resultado.iloc[0] == 2.0  # vA: n_servicos=3, usa gap_relativo, nao 1000/100=10


def test_usa_fallback_de_idade_quando_1_unico_servico() -> None:
    entrada = _entrada_fallback()
    resultado = compute_gap_com_fallback(**entrada)
    assert resultado.iloc[1] == pytest.approx(2.0)  # vB: 300/150
    assert resultado.iloc[3] == pytest.approx(2.0)  # vD: n_servicos=1, ignora gap_relativo=5.0, usa 400/200


def test_sem_intervalo_geral_ainda_pode_sobrar_nulo() -> None:
    entrada = _entrada_fallback()
    resultado = compute_gap_com_fallback(**entrada)
    assert pd.isna(resultado.iloc[2])  # vC: 1 servico, mas modelo sem intervalo_mediano_esperado


def test_intervalo_mediano_geral_preenche_o_residual() -> None:
    entrada = _entrada_fallback()
    resultado = compute_gap_com_fallback(**entrada, intervalo_mediano_geral=200.0)
    assert resultado.iloc[2] == pytest.approx(100.0 / 200.0)  # vC: fallback geral, idade/200


def test_min_servicos_para_gap_proprio_e_parametrizavel() -> None:
    entrada = _entrada_fallback()
    entrada["n_servicos"] = pd.Series([2, 1, 1, 1])
    resultado = compute_gap_com_fallback(**entrada, min_servicos_para_gap_proprio=3)
    assert resultado.iloc[0] == pytest.approx(1000.0 / 100.0)  # 2 servicos nao basta mais, usa fallback


def test_gap_com_fallback_alimenta_em_risco_sem_nulos_quando_completo() -> None:
    entrada = _entrada_fallback()
    gap = compute_gap_com_fallback(**entrada, intervalo_mediano_geral=200.0)
    em_risco = compute_em_risco(gap)
    assert em_risco.isna().sum() == 0
