"""Treina o modelo de risco de evasão a partir das features processadas e grava o artefato em backend/models/."""
from src.application.train_risk_model import (
    FEATURE_COLUMNS,
    compare_thresholds,
    evaluate_auc,
    evaluate_precision_at_k,
    temporal_train_test_split,
    train_decision_tree,
    train_logistic_regression,
)
from src.domain.risk_label import GAP_RELATIVO_THRESHOLD
from src.infrastructure.model_repository import verify_round_trip
from src.interfaces.pipeline.build_features import load_features


def main() -> None:
    tabela = load_features()
    treino, teste, cutoff_date = temporal_train_test_split(tabela, date_col="ultimo_servico")

    if len(treino) == 0 or len(teste) == 0:
        raise ValueError(
            f"split temporal gerou um conjunto vazio (treino={len(treino):,}, teste={len(teste):,}) "
            f"com data de corte {cutoff_date} — ajuste train_fraction ou verifique a distribuicao "
            "de 'ultimo_servico' na tabela de features"
        )

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

    # Reroda a comparação de thresholds a cada treino (em vez de confiar só no valor
    # fixado em risk_label.GAP_RELATIVO_THRESHOLD) — evidência de que 2.0 continua
    # sendo o corte mais plausível se o dataset mudar.
    comparacao_thresholds = compare_thresholds(treino, teste)
    print(f"\nSensibilidade do rótulo a outros thresholds de gap_relativo "
          f"(threshold aplicado em produção: {GAP_RELATIVO_THRESHOLD}):")
    print(comparacao_thresholds.to_string(index=False))

    # Modelo escolhido: LogisticRegression (ver justificativa na issue de comparação).
    X_teste = teste[list(FEATURE_COLUMNS)].dropna()
    destino = verify_round_trip(modelo_logistico, X_teste)
    print(f"Modelo salvo e validado (previsoes identicas antes/depois): {destino}")


if __name__ == "__main__":
    main()
