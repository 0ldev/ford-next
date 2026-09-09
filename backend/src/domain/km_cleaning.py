"""Limpeza de outliers da coluna KM (quilometragem) por winsorização."""
import pandas as pd

DEFAULT_UPPER_PERCENTILE = 0.99


def winsorize_km(km: pd.Series, upper_percentile: float = DEFAULT_UPPER_PERCENTILE) -> pd.Series:
    """Capa valores de KM acima do percentil informado no próprio valor do percentil.

    Valores nulos (NaN) são preservados. `km` não é modificada.
    """
    if not 0 < upper_percentile < 1:
        raise ValueError("upper_percentile deve estar entre 0 e 1 (exclusive)")

    threshold = km.quantile(upper_percentile)
    return km.clip(upper=threshold)
