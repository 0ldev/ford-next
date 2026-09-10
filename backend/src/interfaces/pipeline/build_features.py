"""Lê backend/data/raw/, gera a tabela de features por VIN e grava em backend/data/processed/."""
from pathlib import Path

import pandas as pd

from src.application.build_vehicle_features import (
    build_gap_relativo_table,
    compute_median_service_interval_by_model,
    compute_service_count_and_gap_std,
    compute_vehicle_age_days,
)
from src.domain.risk_label import compute_em_risco, compute_gap_com_fallback
from src.infrastructure.xlsx_reader import (
    DATE_COLUMNS,
    DEDUP_SUBSET,
    normalize_date_columns,
    remove_duplicate_service_orders,
)

RAW_PATH = "data/raw/vin_share.zip"
FEATURES_PATH = "data/processed/vehicle_features.parquet"


def build_features_table(reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Lê o histórico de serviços e monta a tabela de features + rótulo `em_risco` por VIN.

    Inclui `ultimo_servico` (data do serviço mais recente de cada VIN) e `DealerCode`
    (concessionária do serviço mais recente) — a primeira é usada como referência
    temporal no split de treino/teste, a segunda para agrupar leads por concessionária.
    """
    if reference_date is None:
        reference_date = pd.Timestamp.now().normalize()

    df = pd.read_csv(RAW_PATH, compression="zip", low_memory=False)
    df, _ = normalize_date_columns(df, DATE_COLUMNS)
    df, _ = remove_duplicate_service_orders(df, DEDUP_SUBSET)

    tabela = build_gap_relativo_table(df, reference_date=reference_date)

    n_servicos = compute_service_count_and_gap_std(df)[["VIN_Hash", "n_servicos"]]
    idade = compute_vehicle_age_days(
        df.groupby("VIN_Hash", as_index=False)[["SalesDate", "DeliveryDate"]].first(),
        reference_date=reference_date,
    )[["VIN_Hash", "idade_dias"]]

    servicos_ordenados = df.dropna(subset=["ServiceDate"]).sort_values("ServiceDate")
    ultimo_servico = servicos_ordenados.groupby("VIN_Hash")["ServiceDate"].max().rename("ultimo_servico").reset_index()
    dealer_atual = servicos_ordenados.groupby("VIN_Hash")["DealerCode"].last().reset_index()

    tabela = (
        tabela.merge(n_servicos, on="VIN_Hash", how="left")
        .merge(idade, on="VIN_Hash", how="left")
        .merge(ultimo_servico, on="VIN_Hash", how="left")
        .merge(dealer_atual, on="VIN_Hash", how="left")
    )

    intervalo_mediano_geral = compute_median_service_interval_by_model(df)["mediana_dias"].median()
    tabela["gap_com_fallback"] = compute_gap_com_fallback(
        tabela["gap_relativo"],
        tabela["idade_dias"],
        tabela["intervalo_mediano_esperado"],
        tabela["n_servicos"],
        intervalo_mediano_geral=intervalo_mediano_geral,
    )
    tabela["em_risco"] = compute_em_risco(tabela["gap_com_fallback"])

    return tabela


def export_features(tabela: pd.DataFrame, path: str | Path = FEATURES_PATH) -> Path:
    """Grava `tabela` em `path` (parquet, preserva dtypes como `boolean` e `datetime64`)."""
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(destino, index=False)

    return destino


def load_features(path: str | Path = FEATURES_PATH) -> pd.DataFrame:
    """Lê a tabela de features gravada por `export_features`."""
    return pd.read_parquet(path)


def main() -> None:
    tabela = build_features_table()
    destino = export_features(tabela)

    print(f"Tabela de features gerada: {destino} ({len(tabela):,} VINs, {len(tabela.columns)} colunas)")


if __name__ == "__main__":
    main()
