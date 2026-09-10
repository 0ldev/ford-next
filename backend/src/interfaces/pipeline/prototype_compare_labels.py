"""PROTÓTIPO (branch `prototype`): compara o rótulo de risco atual (produção) contra a
versão híbrida com z-score próprio do veículo (`gap_zscore_prototype`).

Só leitura/análise — não grava nada em `data/processed/` nem altera o pipeline de
produção. Roda direto do dataset bruto para não depender de nenhuma mudança no schema
de `vehicle_features.parquet`.
"""
import pandas as pd

from src.application.build_vehicle_features import build_gap_relativo_table
from src.application.gap_zscore_prototype import (
    compute_em_risco_hibrido,
    compute_gap_zscore,
    compute_vehicle_own_gap_stats,
)
from src.domain.risk_label import GAP_RELATIVO_THRESHOLD, compute_em_risco
from src.infrastructure.xlsx_reader import (
    DATE_COLUMNS,
    DEDUP_SUBSET,
    normalize_date_columns,
    remove_duplicate_service_orders,
)

RAW_PATH = "data/raw/vin_share.zip"


def main() -> None:
    df = pd.read_csv(RAW_PATH, compression="zip", low_memory=False)
    df, _ = normalize_date_columns(df, DATE_COLUMNS)
    df, _ = remove_duplicate_service_orders(df, DEDUP_SUBSET)

    tabela = build_gap_relativo_table(df)
    stats_proprio = compute_vehicle_own_gap_stats(df)
    tabela = tabela.merge(stats_proprio, on="VIN_Hash", how="left")

    tabela["gap_zscore"] = compute_gap_zscore(
        tabela["dias_desde_ultimo_servico"], tabela["media_gap_proprio"], tabela["desvio_padrao_gaps"]
    )
    tabela["em_risco_atual"] = compute_em_risco(tabela["gap_relativo"], threshold=GAP_RELATIVO_THRESHOLD)
    tabela["em_risco_hibrido"] = compute_em_risco_hibrido(tabela["gap_zscore"], tabela["gap_relativo"])

    n = len(tabela)
    tem_proprio = tabela["gap_zscore"].notna()

    print(f"Total de VINs: {n:,}")
    print(f"VINs com histórico próprio suficiente p/ z-score (3+ serviços): "
          f"{tem_proprio.sum():,} ({tem_proprio.mean()*100:.1f}%)")
    print()
    print(f"em_risco ATUAL (produção, gap_relativo > {GAP_RELATIVO_THRESHOLD}): "
          f"{tabela['em_risco_atual'].mean(skipna=True)*100:.1f}% da frota")
    print(f"em_risco HÍBRIDO (z-score>1.5 p/ quem tem histórico próprio, "
          f"fallback atual p/ o resto): {tabela['em_risco_hibrido'].mean(skipna=True)*100:.1f}% da frota")
    print()

    sub = tabela[tem_proprio]
    concordam = (sub["em_risco_atual"] == sub["em_risco_hibrido"]).mean() * 100
    print(f"Entre os {tem_proprio.sum():,} VINs com histórico próprio (3+ serviços):")
    print(f"  em_risco atual:   {sub['em_risco_atual'].mean(skipna=True)*100:.1f}%")
    print(f"  em_risco híbrido: {sub['em_risco_hibrido'].mean(skipna=True)*100:.1f}%")
    print(f"  concordância entre os dois rótulos: {concordam:.1f}%")

    destacados = sub[sub["em_risco_atual"].fillna(False) & ~sub["em_risco_hibrido"].fillna(False)]
    print(f"\nVINs que o rótulo ATUAL marca 'em risco' mas o HÍBRIDO não "
          f"(o caso 'errático mas fiel' que o protótipo tenta corrigir): {len(destacados):,} "
          f"({len(destacados) / len(sub) * 100:.1f}% de quem tem histórico próprio)")

    inverso = sub[~sub["em_risco_atual"].fillna(False) & sub["em_risco_hibrido"].fillna(False)]
    print(f"VINs que o HÍBRIDO marca 'em risco' mas o ATUAL não "
          f"(padrão regular, mas atualmente bem fora do próprio normal): {len(inverso):,} "
          f"({len(inverso) / len(sub) * 100:.1f}% de quem tem histórico próprio)")

    if len(destacados) > 0:
        exemplo = destacados.iloc[0]
        print(f"\nExemplo concreto: VIN com dias_desde_ultimo_servico="
              f"{exemplo['dias_desde_ultimo_servico']:.0f}, "
              f"intervalo_mediano_esperado (modelo)={exemplo['intervalo_mediano_esperado']:.0f}, "
              f"média própria={exemplo['media_gap_proprio']:.0f}, "
              f"desvio próprio={exemplo['desvio_padrao_gaps']:.0f} "
              f"-> gap_relativo={exemplo['gap_relativo']:.2f} (marcado em risco), "
              f"gap_zscore={exemplo['gap_zscore']:.2f} (não marcado)")


if __name__ == "__main__":
    main()
