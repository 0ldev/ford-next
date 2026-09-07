"""Lê backend/data/raw/, gera a tabela de features por VIN e grava em backend/data/processed/."""
import pandas as pd

RAW_PATH = "data/raw/vin_share.zip"


def explore(df: pd.DataFrame) -> None:
    print("=== Contagens gerais ===")
    print("Total de linhas:", len(df))
    print("VINs únicos:", df["VIN_Hash"].nunique())
    print("Concessionárias únicas (DealerCode):", df["DealerCode"].nunique())
    print("Modelos únicos (ModelName):", df["ModelName"].nunique())

    print("\n=== Distribuição por modelo (top 10) ===")
    print(df["ModelName"].value_counts().head(10))

    service_dates = pd.to_datetime(df["ServiceDate"], errors="coerce")
    print("\n=== Intervalo de datas de serviço ===")
    print("Min:", service_dates.min(), "Max:", service_dates.max())
    print("Nulos:", service_dates.isna().sum())

    print("\n=== Estatísticas de KM ===")
    km = df["KM"]
    print(km.describe())
    for p in [0.95, 0.99, 0.999]:
        print(f"percentil {p}: {km.quantile(p)}")
    print("linhas acima do p99:", (km > km.quantile(0.99)).sum())

    print("\n=== Serviços por VIN ===")
    counts = df.groupby("VIN_Hash").size()
    print("média:", counts.mean(), "mediana:", counts.median(), "máximo:", counts.max())
    print("% VINs com apenas 1 serviço:", (counts == 1).mean() * 100)

    print("\n=== Intervalo mediano entre serviços por modelo (dias) ===")
    df2 = df.copy()
    df2["ServiceDate"] = service_dates
    df2 = df2.dropna(subset=["ServiceDate"]).sort_values(["VIN_Hash", "ServiceDate"])
    gaps = df2.groupby("VIN_Hash")["ServiceDate"].diff().dt.days
    df2["gap_dias"] = gaps
    modelo_por_vin = df2.groupby("VIN_Hash")["ModelName"].first()
    df2["Modelo"] = df2["VIN_Hash"].map(modelo_por_vin)
    mediana_por_modelo = df2.dropna(subset=["gap_dias"]).groupby("Modelo")["gap_dias"].median().sort_values()
    print(mediana_por_modelo)


def main() -> None:
    df = pd.read_csv(RAW_PATH, compression="zip")
    explore(df)


if __name__ == "__main__":
    main()
