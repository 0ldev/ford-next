import pandas as pd
import pytest

from src.application.leads_metrics import compute_score_distribution


def _leads(scores: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"score": scores})


def test_compute_score_distribution_agrupa_em_faixas_de_10_pontos() -> None:
    resultado = compute_score_distribution(_leads([0.0, 0.05, 0.15, 0.95, 1.0]), n_faixas=10)

    por_faixa = {(f["faixaInicio"], f["faixaFim"]): f["quantidade"] for f in resultado}
    assert por_faixa[(0.0, 10.0)] == 2  # 0.0, 0.05
    assert por_faixa[(10.0, 20.0)] == 1  # 0.15
    assert por_faixa[(90.0, 100.0)] == 2  # 0.95, 1.0


def test_compute_score_distribution_primeira_faixa_comeca_em_zero_nao_negativo() -> None:
    # pd.cut(include_lowest=True) desloca a borda esquerda do primeiro intervalo pra
    # um pouco abaixo de 0 internamente (ex.: -0.001) soh pra incluir o 0.0 no
    # intervalo semiaberto -- isso nao pode vazar pro valor exibido.
    resultado = compute_score_distribution(_leads([0.0]), n_faixas=10)

    primeira_faixa = min(resultado, key=lambda f: f["faixaInicio"])
    assert primeira_faixa["faixaInicio"] == 0.0


def test_compute_score_distribution_retorna_todas_as_faixas_mesmo_vazias() -> None:
    resultado = compute_score_distribution(_leads([0.0, 1.0]), n_faixas=10)

    assert len(resultado) == 10
    assert sum(f["quantidade"] for f in resultado) == 2


def test_compute_score_distribution_faixas_em_ordem_crescente() -> None:
    resultado = compute_score_distribution(_leads([0.0, 0.5, 1.0]), n_faixas=10)

    inicios = [f["faixaInicio"] for f in resultado]
    assert inicios == sorted(inicios)


def test_compute_score_distribution_e_bimodal_com_dados_realistas() -> None:
    # Reflete o formato real descrito em domain/action_rules.py: a maior parte da
    # frota perto de 0% ou perto de 100%, quase nada no meio.
    scores = [0.0] * 27 + [0.5] * 2 + [1.0] * 71
    resultado = compute_score_distribution(_leads(scores), n_faixas=10)

    por_faixa = {(f["faixaInicio"], f["faixaFim"]): f["quantidade"] for f in resultado}
    assert por_faixa[(0.0, 10.0)] == 27
    assert por_faixa[(90.0, 100.0)] == 71
    # faixas fechadas a direita ((40,50]): 0.5 cai na faixa 40-50, nao na 50-60.
    assert por_faixa[(40.0, 50.0)] == 2
    assert por_faixa[(50.0, 60.0)] == 0


def test_compute_score_distribution_numero_de_faixas_e_parametrizavel() -> None:
    resultado = compute_score_distribution(_leads([0.0, 1.0]), n_faixas=4)

    assert len(resultado) == 4
    assert [f["faixaFim"] for f in resultado] == [25.0, 50.0, 75.0, 100.0]
