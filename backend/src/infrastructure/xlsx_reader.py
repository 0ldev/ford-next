"""Leitura de planilhas e normalização de colunas de data para datetime do pandas."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

DATE_COLUMNS: tuple[str, ...] = (
    "ServiceDate",
    "SalesDate",
    "DeliveryDate",
    "WarrantyStartDate",
)

# Duas linhas são a mesma ordem de serviço se compartilham VIN, data de serviço e
# tipo de serviço: é o conjunto mínimo de colunas que identifica "o mesmo carro
# fez o mesmo tipo de serviço no mesmo dia", o que cobre o caso real de reimportação/
# duplicidade de sincronização do sistema da concessionária sem descartar visitas
# genuinamente distintas (dia diferente ou tipo de serviço diferente).
DEDUP_SUBSET: tuple[str, ...] = ("VIN_Hash", "ServiceDate", "ServiceType")


def normalize_date_columns(
    df: pd.DataFrame, columns: Iterable[str] = DATE_COLUMNS
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Converte as colunas informadas para datetime do pandas.

    Valores nulos ou mal formatados viram `NaT` (via `errors="coerce"`) em vez de
    levantar exceção. `df` não é modificado.

    Retorna uma cópia do DataFrame com as colunas convertidas e um relatório com a
    quantidade de valores nulos/inválidos (`NaT`) por coluna após a conversão.
    """
    result = df.copy()
    report: dict[str, int] = {}

    for column in columns:
        parsed = pd.to_datetime(result[column], errors="coerce")
        result[column] = parsed
        report[column] = int(parsed.isna().sum())

    return result, report


def remove_duplicate_service_orders(
    df: pd.DataFrame, subset: Iterable[str] = DEDUP_SUBSET
) -> tuple[pd.DataFrame, int]:
    """Remove ordens de serviço duplicadas (mesmo VIN + mesma data de serviço + mesmo tipo de serviço).

    Mantém a primeira ocorrência de cada duplicata. `df` não é modificado.

    Retorna o DataFrame deduplicado (índice reiniciado) e a quantidade de linhas removidas.
    """
    subset = list(subset)
    n_before = len(df)
    result = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
    n_removed = n_before - len(result)

    return result, n_removed


def read_xlsx(
    path: str | Path,
    date_columns: Iterable[str] = DATE_COLUMNS,
    dedup_subset: Iterable[str] = DEDUP_SUBSET,
) -> tuple[pd.DataFrame, dict[str, int], int]:
    """Lê uma planilha xlsx, normaliza as colunas de data e remove ordens de serviço duplicadas.

    A deduplicação roda depois da normalização de datas, para comparar por valor de
    data real (`datetime`) em vez de string bruta.
    """
    df = pd.read_excel(path)
    df, date_report = normalize_date_columns(df, date_columns)
    df, n_duplicates_removed = remove_duplicate_service_orders(df, dedup_subset)
    return df, date_report, n_duplicates_removed
