"""Lê backend/data/raw/, normaliza e deduplica o histórico de serviços, grava em backend/data/processed/."""
from pathlib import Path

import pandas as pd

from src.infrastructure.xlsx_reader import (
    DATE_COLUMNS,
    DEDUP_SUBSET,
    normalize_date_columns,
    remove_duplicate_service_orders,
)

RAW_PATH = "data/raw/vin_share.zip"
SERVICE_HISTORY_PATH = "data/processed/service_history.parquet"


def build_service_history() -> pd.DataFrame:
    """Lê o histórico de serviços bruto, normaliza datas e remove ordens duplicadas.

    Granularidade de ordem de serviço (uma linha por VIN x serviço) — diferente de
    `build_features.build_features_table` (uma linha por VIN). É a base do endpoint
    `GET /api/vin-share`, que precisa filtrar por `ServiceType` e por período de
    serviço, granularidade que a tabela de features (agregada por VIN) não tem.
    """
    df = pd.read_csv(RAW_PATH, compression="zip", low_memory=False)
    df, _ = normalize_date_columns(df, DATE_COLUMNS)
    df, _ = remove_duplicate_service_orders(df, DEDUP_SUBSET)

    return df


def export_service_history(df: pd.DataFrame, path: str | Path = SERVICE_HISTORY_PATH) -> Path:
    """Grava `df` em `path` (parquet, preserva as colunas de data como `datetime64`)."""
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(destino, index=False)

    return destino


def main() -> None:
    df = build_service_history()
    destino = export_service_history(df)

    print(f"Histórico de serviços gerado: {destino} ({len(df):,} ordens de serviço)")


if __name__ == "__main__":
    main()
