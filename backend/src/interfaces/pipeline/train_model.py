"""Treina o modelo de risco de evasão a partir das features processadas e grava o artefato em backend/models/."""
import pandas as pd

from src.application.build_vehicle_features import (
    build_gap_relativo_table,
    compute_median_service_interval_by_model,
    compute_service_count_and_gap_std,
    compute_vehicle_age_days,
)
from src.application.train_risk_model import (
    FEATURE_COLUMNS,
    evaluate_auc,
    evaluate_precision_at_k,
    temporal_train_test_split,
    train_decision_tree,
    train_logistic_regression,
)
from src.domain.risk_label import compute_em_risco, compute_gap_com_fallback
from src.infrastructure.model_repository import verify_round_trip
from src.infrastructure.xlsx_reader import (
    DATE_COLUMNS,
    DEDUP_SUBSET,
    normalize_date_columns,
    remove_duplicate_service_orders,
)

RAW_PATH = "data/raw/vin_share.zip"


def build_dataset(reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Lê o histórico de serviços e monta a tabela de features + rótulo `em_risco` por VIN.

    Inclui `ultimo_servico` (data do serviço mais recente de cada VIN) — é a coluna
    usada como referência temporal no split de treino/teste.
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
    ultimo_servico = df.groupby("VIN_Hash")["ServiceDate"].max().rename("ultimo_servico").reset_index()

    tabela = (
        tabela.merge(n_servicos, on="VIN_Hash", how="left")
        .merge(idade, on="VIN_Hash", how="left")
        .merge(ultimo_servico, on="VIN_Hash", how="left")
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


def main() -> None:
    tabela = build_dataset()
    treino, teste, cutoff_date = temporal_train_test_split(tabela, date_col="ultimo_servico")

    print(f"Total de VINs: {len(tabela):,}")
    print(f"Data de corte (80% do período): {cutoff_date}")
    print(
        f"Treino: {len(treino):,} VINs "
        f"({treino['ultimo_servico'].min().date()} a {treino['ultimo_servico'].max().date()})"
    )
    print(
        f"Teste:  {len(teste):,} VINs "
        f"({teste['ultimo_servico'].min().date()} a {teste['ultimo_servico'].max().date()})"
    )

    assert treino["ultimo_servico"].max() <= teste["ultimo_servico"].min(), (
        "vazamento de dados futuros no treino: ha VIN de treino com ultimo_servico "
        "mais recente que o VIN mais antigo do teste"
    )
    print("OK - sem vazamento de dados futuros no treino (max(treino) <= min(teste)).")

    modelo_logistico = train_logistic_regression(treino)
    auc_logistico = evaluate_auc(modelo_logistico, teste)

    modelo_arvore = train_decision_tree(treino)
    auc_arvore = evaluate_auc(modelo_arvore, teste)

    print(f"AUC LogisticRegression (baseline): {auc_logistico:.4f}")
    print(f"AUC DecisionTree (max_depth={modelo_arvore.get_depth()}):     {auc_arvore:.4f}")

    # Validação temporal do modelo escolhido (LogisticRegression) no conjunto de
    # teste — período posterior à data de corte.
    precisao_top10 = evaluate_precision_at_k(modelo_logistico, teste, k_fraction=0.10)
    precisao_top20 = evaluate_precision_at_k(modelo_logistico, teste, k_fraction=0.20)
    print(f"Precision@top-10% (LogisticRegression): {precisao_top10:.4f}")
    print(f"Precision@top-20% (LogisticRegression): {precisao_top20:.4f}")

    # Modelo escolhido: LogisticRegression (ver justificativa na issue de comparação).
    X_teste = teste[list(FEATURE_COLUMNS)].dropna()
    destino = verify_round_trip(modelo_logistico, X_teste)
    print(f"Modelo salvo e validado (previsoes identicas antes/depois): {destino}")


if __name__ == "__main__":
    main()
