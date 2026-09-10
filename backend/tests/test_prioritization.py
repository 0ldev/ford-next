import pandas as pd
import pytest

from src.domain.prioritization import (
    VALOR_CLIENTE_TETO,
    compute_prioridade,
    compute_valor_cliente,
)


def test_valor_cliente_cresce_com_n_servicos() -> None:
    resultado = compute_valor_cliente(pd.Series([1, 4, 8]))
    assert resultado.tolist() == [1 / 8, 4 / 8, 1.0]


def test_valor_cliente_satura_no_teto() -> None:
    resultado = compute_valor_cliente(pd.Series([8, 35]))
    assert resultado.iloc[0] == resultado.iloc[1] == 1.0


def test_valor_cliente_teto_e_parametrizavel() -> None:
    resultado = compute_valor_cliente(pd.Series([5]), teto=10)
    assert resultado.iloc[0] == 0.5


def test_valor_cliente_nulo_quando_n_servicos_nulo() -> None:
    resultado = compute_valor_cliente(pd.Series([None]))
    assert resultado.isna().all()


def test_prioridade_maxima_quando_risco_e_valor_sao_maximos() -> None:
    assert compute_prioridade(pd.Series([1.0]), pd.Series([1.0])).iloc[0] == 1.0


def test_prioridade_minima_quando_risco_e_valor_sao_minimos() -> None:
    assert compute_prioridade(pd.Series([0.0]), pd.Series([0.0])).iloc[0] == 0.0


def test_risco_pesa_mais_que_valor_por_padrao() -> None:
    # risco alto/valor baixo deve ficar à frente de risco medio/valor alto
    risco_alto_valor_baixo = compute_prioridade(pd.Series([1.0]), pd.Series([0.0])).iloc[0]
    risco_medio_valor_alto = compute_prioridade(pd.Series([0.5]), pd.Series([1.0])).iloc[0]

    assert risco_alto_valor_baixo > risco_medio_valor_alto


def test_pesos_sao_parametrizaveis() -> None:
    resultado = compute_prioridade(pd.Series([1.0]), pd.Series([0.0]), peso_risco=0.5, peso_valor=0.5)
    assert resultado.iloc[0] == 0.5


def test_prioridade_nula_quando_algum_dos_dois_sinais_e_nulo() -> None:
    assert compute_prioridade(pd.Series([None]), pd.Series([1.0])).isna().all()
    assert compute_prioridade(pd.Series([1.0]), pd.Series([None])).isna().all()


# --- Validação com 5 exemplos reais (data/processed/leads.csv + vehicle_features.parquet) ---
# Cobrem as 4 combinações da matriz risco x valor, mais um caso misto no meio.

def _prioridade_exemplo(score: float, n_servicos: int) -> float:
    valor = compute_valor_cliente(pd.Series([n_servicos])).iloc[0]
    return compute_prioridade(pd.Series([score]), pd.Series([valor])).iloc[0]


def test_exemplo_real_alto_risco_alto_valor_e_o_mais_prioritario() -> None:
    # RANGER, score=1.0, n_servicos=9 (>= teto) -> prioridade máxima (1.0)
    assert _prioridade_exemplo(score=1.0, n_servicos=9) == pytest.approx(1.0)


def test_exemplo_real_alto_risco_baixo_valor_fica_atras_do_alto_valor() -> None:
    # MUSTANG MACH-E, score=1.0, n_servicos=1 (1º serviço)
    alto_valor = _prioridade_exemplo(score=1.0, n_servicos=9)
    baixo_valor = _prioridade_exemplo(score=1.0, n_servicos=1)

    assert baixo_valor == pytest.approx(0.7375)
    assert baixo_valor < alto_valor


def test_exemplo_real_baixo_risco_alto_valor_ainda_fica_a_frente_do_baixo_valor() -> None:
    # RANGER, score=0.0098, n_servicos=8 -> valor alto compensa parcialmente o risco baixo
    baixo_risco_alto_valor = _prioridade_exemplo(score=0.0098, n_servicos=8)
    baixo_risco_baixo_valor = _prioridade_exemplo(score=0.0, n_servicos=1)

    assert baixo_risco_alto_valor > baixo_risco_baixo_valor


def test_exemplo_real_baixo_risco_baixo_valor_e_o_menos_prioritario() -> None:
    # MUSTANG MACH-E, score=0.0, n_servicos=1 -> prioridade quase nula
    assert _prioridade_exemplo(score=0.0, n_servicos=1) == pytest.approx(0.0375)


def test_exemplo_real_risco_medio_fica_entre_os_extremos() -> None:
    # RANGER, score=0.619, n_servicos=3 -> nem o topo nem o fim da fila
    medio = _prioridade_exemplo(score=0.619, n_servicos=3)
    topo = _prioridade_exemplo(score=1.0, n_servicos=9)
    fim = _prioridade_exemplo(score=0.0, n_servicos=1)

    assert fim < medio < topo
