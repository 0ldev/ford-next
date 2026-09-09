import pandas as pd
import pytest

from src.domain.km_cleaning import winsorize_km

# 101 valores (1..100 normais + 1 outlier extremo) para que o percentil 99
# recaia exatamente sobre o valor 100 (posição inteira: 0.99 * (101 - 1) = 99).
NORMAL_VALUES = list(range(1, 101))
EXTREME_OUTLIER = 10_000_000.0
LIMIT_VALUE = 100.0


@pytest.fixture
def km_series() -> pd.Series:
    return pd.Series(NORMAL_VALUES + [EXTREME_OUTLIER])


def test_valor_normal_permanece_inalterado(km_series: pd.Series) -> None:
    cleaned = winsorize_km(km_series)
    assert cleaned.iloc[49] == NORMAL_VALUES[49]  # 50, bem abaixo do limite


def test_valor_exatamente_no_limite_permanece_inalterado(km_series: pd.Series) -> None:
    cleaned = winsorize_km(km_series)
    assert cleaned.iloc[99] == LIMIT_VALUE  # 100, igual ao percentil 99 calculado


def test_outlier_extremo_e_capado_no_percentil(km_series: pd.Series) -> None:
    cleaned = winsorize_km(km_series)
    assert cleaned.iloc[-1] == LIMIT_VALUE  # 10_000_000 -> capado para 100.0


def test_nulos_sao_preservados() -> None:
    km = pd.Series(NORMAL_VALUES + [None])
    cleaned = winsorize_km(km)
    assert pd.isna(cleaned.iloc[-1])


def test_upper_percentile_invalido_gera_erro(km_series: pd.Series) -> None:
    with pytest.raises(ValueError):
        winsorize_km(km_series, upper_percentile=1.5)
