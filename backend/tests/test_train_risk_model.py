import numpy as np
import pandas as pd
import pytest

from src.application.train_risk_model import (
    compute_cutoff_date,
    evaluate_auc,
    evaluate_precision_at_k,
    precision_at_top_k,
    temporal_train_test_split,
    train_decision_tree,
    train_logistic_regression,
)


def _df_10_dias() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": [f"v{i}" for i in range(10)],
        "data": pd.date_range("2024-01-01", periods=10, freq="D"),
    })


def test_cutoff_date_e_o_quantil_da_fracao_de_treino() -> None:
    dates = pd.to_datetime([f"2024-01-{d:02d}" for d in range(1, 11)])  # 1..10 jan
    cutoff = compute_cutoff_date(pd.Series(dates), train_fraction=0.8)
    assert cutoff == pd.Timestamp("2024-01-08 04:48:00")  # quantil 0.8 interpolado


def test_cutoff_date_ignora_nulos() -> None:
    dates = pd.Series(pd.to_datetime(["2024-01-01", None, "2024-01-10"]))
    cutoff = compute_cutoff_date(dates, train_fraction=0.5)
    assert cutoff == pd.Timestamp("2024-01-01") + (pd.Timestamp("2024-01-10") - pd.Timestamp("2024-01-01")) / 2


def test_train_fraction_invalido_gera_erro() -> None:
    with pytest.raises(ValueError):
        compute_cutoff_date(pd.Series(pd.to_datetime(["2024-01-01"])), train_fraction=1.5)


def test_split_sem_sobreposicao_de_datas() -> None:
    treino, teste, cutoff = temporal_train_test_split(_df_10_dias(), date_col="data")

    assert treino["data"].max() <= cutoff
    assert teste["data"].min() > cutoff
    assert treino["data"].max() <= teste["data"].min()  # a prova central de "sem vazamento"


def test_split_nao_perde_nem_duplica_linhas() -> None:
    df = _df_10_dias()
    treino, teste, _ = temporal_train_test_split(df, date_col="data")

    assert len(treino) + len(teste) == len(df)
    assert set(treino["VIN_Hash"]) | set(teste["VIN_Hash"]) == set(df["VIN_Hash"])
    assert set(treino["VIN_Hash"]) & set(teste["VIN_Hash"]) == set()


def test_split_respeita_fracao_de_treino_aproximada() -> None:
    treino, teste, _ = temporal_train_test_split(_df_10_dias(), date_col="data", train_fraction=0.8)

    assert len(treino) == 8  # 1..8 jan (cutoff cai em 08/01 04:48)
    assert len(teste) == 2  # 9..10 jan


def test_cutoff_date_explicito_ignora_train_fraction() -> None:
    treino, teste, cutoff = temporal_train_test_split(
        _df_10_dias(), date_col="data", cutoff_date=pd.Timestamp("2024-01-05")
    )

    assert cutoff == pd.Timestamp("2024-01-05")
    assert len(treino) == 5
    assert len(teste) == 5


def test_linhas_com_data_nula_sao_descartadas() -> None:
    df = _df_10_dias()
    df = pd.concat([df, pd.DataFrame({"VIN_Hash": ["vX"], "data": [pd.NaT]})], ignore_index=True)

    treino, teste, _ = temporal_train_test_split(df, date_col="data")

    assert "vX" not in set(treino["VIN_Hash"]) | set(teste["VIN_Hash"])
    assert len(treino) + len(teste) == 10


def test_dataframe_original_nao_e_modificado() -> None:
    df = _df_10_dias()
    original = df.copy()

    temporal_train_test_split(df, date_col="data")

    pd.testing.assert_frame_equal(df, original)


def _dataset_sintetico(n: int = 200, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    gap_com_fallback = rng.uniform(0, 5, n)
    return pd.DataFrame({
        "idade_dias": rng.uniform(30, 3000, n),
        "gap_com_fallback": gap_com_fallback,
        "n_servicos": rng.integers(1, 20, n),
        "em_risco": gap_com_fallback > 1.5,  # mesma regra de risk_label.compute_em_risco
    })


def test_train_logistic_regression_treina_sem_erro() -> None:
    modelo = train_logistic_regression(_dataset_sintetico())
    assert hasattr(modelo, "predict_proba")


def test_evaluate_auc_retorna_valor_no_intervalo_valido() -> None:
    df = _dataset_sintetico(seed=1)
    treino, teste = df.iloc[:150], df.iloc[150:]

    modelo = train_logistic_regression(treino)
    auc = evaluate_auc(modelo, teste)

    assert 0.0 <= auc <= 1.0


def test_auc_alta_quando_label_e_bem_separavel_pelas_features() -> None:
    df = _dataset_sintetico(seed=2, n=400)
    treino, teste = df.iloc[:300], df.iloc[300:]

    modelo = train_logistic_regression(treino)
    auc = evaluate_auc(modelo, teste)

    assert auc > 0.9


def test_linhas_com_feature_nula_nao_quebram_o_treino() -> None:
    df = _dataset_sintetico(seed=3)
    df.loc[0, "idade_dias"] = None

    modelo = train_logistic_regression(df)

    assert hasattr(modelo, "predict_proba")


def test_train_e_evaluate_nao_modificam_os_dataframes_originais() -> None:
    df = _dataset_sintetico(seed=4)
    treino, teste = df.iloc[:150].copy(), df.iloc[150:].copy()
    treino_original, teste_original = treino.copy(), teste.copy()

    modelo = train_logistic_regression(treino)
    evaluate_auc(modelo, teste)

    pd.testing.assert_frame_equal(treino, treino_original)
    pd.testing.assert_frame_equal(teste, teste_original)


def test_train_decision_tree_treina_sem_erro() -> None:
    modelo = train_decision_tree(_dataset_sintetico())
    assert hasattr(modelo, "predict_proba")


def test_decision_tree_respeita_max_depth_configurado() -> None:
    modelo = train_decision_tree(_dataset_sintetico(seed=5), max_depth=3)
    assert modelo.get_depth() <= 3


def test_decision_tree_auc_no_intervalo_valido_e_com_dataset_separavel() -> None:
    df = _dataset_sintetico(seed=6, n=400)
    treino, teste = df.iloc[:300], df.iloc[300:]

    modelo = train_decision_tree(treino)
    auc = evaluate_auc(modelo, teste)

    assert 0.0 <= auc <= 1.0
    assert auc > 0.9  # mesma regra deterministica de rotulo do teste de LogisticRegression


def test_decision_tree_nao_modifica_o_dataframe_original() -> None:
    df = _dataset_sintetico(seed=7)
    original = df.copy()

    train_decision_tree(df)

    pd.testing.assert_frame_equal(df, original)


def test_precision_at_top_k_com_ranking_perfeito() -> None:
    y_true = pd.Series([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    y_score = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0])

    assert precision_at_top_k(y_true, y_score, k_fraction=0.1) == 1.0  # top 1: so positivos
    assert precision_at_top_k(y_true, y_score, k_fraction=0.3) == 1.0  # top 3: os 3 positivos


def test_precision_at_top_k_com_ranking_misto() -> None:
    y_true = pd.Series([1, 0, 1, 0, 1, 0, 0, 0, 0, 0])
    y_score = np.array([0.9, 0.85, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])

    # top 40% (k=4): indices 0,1,2,3 -> y_true [1,0,1,0] -> 2 de 4
    assert precision_at_top_k(y_true, y_score, k_fraction=0.4) == pytest.approx(0.5)


def test_precision_at_top_k_arredonda_k_para_cima() -> None:
    y_true = pd.Series([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    y_score = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0])

    # 5% de 10 = 0.5 -> ceil = 1 linha (nao 0)
    assert precision_at_top_k(y_true, y_score, k_fraction=0.05) == 1.0


def test_precision_at_top_k_fracao_invalida_gera_erro() -> None:
    y_true = pd.Series([1, 0])
    y_score = np.array([0.9, 0.1])

    with pytest.raises(ValueError):
        precision_at_top_k(y_true, y_score, k_fraction=0.0)
    with pytest.raises(ValueError):
        precision_at_top_k(y_true, y_score, k_fraction=1.5)


def test_evaluate_precision_at_k_no_intervalo_valido() -> None:
    df = _dataset_sintetico(seed=8, n=400)
    treino, teste = df.iloc[:300], df.iloc[300:]

    modelo = train_logistic_regression(treino)
    precisao = evaluate_precision_at_k(modelo, teste, k_fraction=0.2)

    assert 0.0 <= precisao <= 1.0
    assert precisao > 0.9  # mesma regra deterministica de rotulo dos outros testes
