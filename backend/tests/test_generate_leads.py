import numpy as np
import pandas as pd
import pytest

from src.application.generate_leads import add_risk_explanation, compute_score_risco, explain_risk, rank_by_dealer
from src.application.train_risk_model import FEATURE_COLUMNS


class _ModeloFixo:
    """Stub: sempre retorna a mesma probabilidade de risco (0.99), independente da entrada."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.full((len(X), 2), [0.01, 0.99])


def _tabela_segmentacao() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": ["v1", "v2", "v3", "v4"],
        "ModelName": ["RANGER", "KA", "ECOSPORT", "FOCUS"],
        "idade_dias": [500.0, 500.0, 500.0, 500.0],
        "gap_com_fallback": [2.5, 0.5, 2.5, 0.5],  # acima/abaixo do threshold padrao (2.0)
        "n_servicos": [3, 3, 3, 3],
    })


def test_compute_score_risco_usa_modelo_de_ml_para_ranger_e_ka() -> None:
    resultado = compute_score_risco(_tabela_segmentacao(), _ModeloFixo(), FEATURE_COLUMNS).set_index("VIN_Hash")

    assert resultado.loc["v1", "score_risco"] == pytest.approx(0.99)  # RANGER
    assert resultado.loc["v2", "score_risco"] == pytest.approx(0.99)  # KA


def test_compute_score_risco_usa_heuristica_para_os_demais_modelos() -> None:
    resultado = compute_score_risco(_tabela_segmentacao(), _ModeloFixo(), FEATURE_COLUMNS).set_index("VIN_Hash")

    assert resultado.loc["v3", "score_risco"] == 1.0  # ECOSPORT, gap 2.5 > threshold 2.0
    assert resultado.loc["v4", "score_risco"] == 0.0  # FOCUS, gap 0.5 <= threshold 2.0


def test_compute_score_risco_modelos_com_ml_e_parametrizavel() -> None:
    resultado = compute_score_risco(
        _tabela_segmentacao(), _ModeloFixo(), FEATURE_COLUMNS, modelos_com_ml=("ECOSPORT",)
    ).set_index("VIN_Hash")

    assert resultado.loc["v3", "score_risco"] == pytest.approx(0.99)  # ECOSPORT agora usa ML
    assert resultado.loc["v1", "score_risco"] == 1.0  # RANGER cai na heuristica: gap 2.5 > 2.0


def test_compute_score_risco_nao_modifica_o_dataframe_original() -> None:
    df = _tabela_segmentacao()
    original = df.copy()

    compute_score_risco(df, _ModeloFixo(), FEATURE_COLUMNS)

    pd.testing.assert_frame_equal(df, original)


def test_compute_score_risco_nao_quebra_com_segmento_ml_vazio() -> None:
    """Sem nenhum VIN de RANGER/KA no lote (ex.: filtro por concessionária/modelo),
    nao pode chamar predict_proba com um DataFrame vazio (StandardScaler rejeita)."""
    tabela = _tabela_segmentacao()
    so_heuristica = tabela[~tabela["ModelName"].isin(("RANGER", "KA"))].copy()

    resultado = compute_score_risco(so_heuristica, _ModeloFixo(), FEATURE_COLUMNS).set_index("VIN_Hash")

    assert resultado.loc["v3", "score_risco"] == 1.0
    assert resultado.loc["v4", "score_risco"] == 0.0


def test_compute_score_risco_nao_quebra_com_segmento_heuristica_vazio() -> None:
    tabela = _tabela_segmentacao()
    so_ml = tabela[tabela["ModelName"].isin(("RANGER", "KA"))].copy()

    resultado = compute_score_risco(so_ml, _ModeloFixo(), FEATURE_COLUMNS).set_index("VIN_Hash")

    assert resultado.loc["v1", "score_risco"] == pytest.approx(0.99)
    assert resultado.loc["v2", "score_risco"] == pytest.approx(0.99)


def _leads_df() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": ["v1", "v2", "v3", "v4", "v5", "v6"],
        "DealerCode": [1, 1, 1, 2, 2, 2],
        "score_risco": [0.9, 0.5, 0.7, 0.3, 0.3, 0.8],
    })


def test_rank_1_e_o_maior_score_dentro_do_grupo() -> None:
    resultado = rank_by_dealer(_leads_df()).set_index("VIN_Hash")

    assert resultado.loc["v1", "rank_concessionaria"] == 1  # dealer 1: 0.9 e o maior
    assert resultado.loc["v6", "rank_concessionaria"] == 1  # dealer 2: 0.8 e o maior


def test_rank_reinicia_em_cada_concessionaria() -> None:
    resultado = rank_by_dealer(_leads_df())

    for dealer in resultado["DealerCode"].unique():
        ranks = resultado.loc[resultado["DealerCode"] == dealer, "rank_concessionaria"]
        assert ranks.min() == 1


def test_ordem_do_ranking_dentro_do_grupo() -> None:
    resultado = rank_by_dealer(_leads_df()).set_index("VIN_Hash")

    # dealer 1: v1 (0.9) > v3 (0.7) > v2 (0.5)
    assert resultado.loc["v1", "rank_concessionaria"] < resultado.loc["v3", "rank_concessionaria"]
    assert resultado.loc["v3", "rank_concessionaria"] < resultado.loc["v2", "rank_concessionaria"]


def test_empates_recebem_o_mesmo_rank() -> None:
    resultado = rank_by_dealer(_leads_df()).set_index("VIN_Hash")

    # dealer 2: v4 e v5 empatados em 0.3 -> ambos rank 2 (v6=0.8 e rank 1)
    assert resultado.loc["v4", "rank_concessionaria"] == resultado.loc["v5", "rank_concessionaria"] == 2


def test_resultado_ordenado_por_dealer_e_rank() -> None:
    resultado = rank_by_dealer(_leads_df())

    assert resultado["DealerCode"].tolist() == sorted(resultado["DealerCode"].tolist())
    for dealer in resultado["DealerCode"].unique():
        ranks_do_grupo = resultado.loc[resultado["DealerCode"] == dealer, "rank_concessionaria"].tolist()
        assert ranks_do_grupo == sorted(ranks_do_grupo)


def test_dataframe_original_nao_e_modificado() -> None:
    df = _leads_df()
    original = df.copy()

    rank_by_dealer(df)

    pd.testing.assert_frame_equal(df, original)


def test_nomes_de_coluna_customizaveis() -> None:
    df = _leads_df().rename(columns={"DealerCode": "loja", "score_risco": "prob"})
    resultado = rank_by_dealer(df, dealer_col="loja", score_col="prob", rank_col="posicao")

    assert "posicao" in resultado.columns
    assert resultado.loc[resultado["loja"] == 1, "posicao"].min() == 1


def test_explain_risk_frase_do_exemplo_da_issue() -> None:
    assert explain_risk(180, 1.4) == "180 dias sem serviço, 40% acima do intervalo esperado do modelo"


def test_explain_risk_arredonda_dias_e_percentual() -> None:
    assert explain_risk(180.4, 1.403) == "180 dias sem serviço, 40% acima do intervalo esperado do modelo"


def test_explain_risk_singular_de_1_dia() -> None:
    assert explain_risk(1, 1.5) == "1 dia sem serviço, 50% acima do intervalo esperado do modelo"


def test_explain_risk_abaixo_do_intervalo_esperado() -> None:
    assert explain_risk(30, 0.5) == "30 dias sem serviço, 50% abaixo do intervalo esperado do modelo"


def test_explain_risk_exatamente_no_intervalo_esperado() -> None:
    assert explain_risk(90, 1.0) == "90 dias sem serviço, dentro do intervalo esperado do modelo"


def test_explain_risk_com_valor_nulo_nao_quebra() -> None:
    assert explain_risk(None, 1.4) == "dados insuficientes para explicar o risco deste veículo"
    assert explain_risk(180, None) == "dados insuficientes para explicar o risco deste veículo"


def test_add_risk_explanation_adiciona_coluna_sem_modificar_original() -> None:
    df = pd.DataFrame({
        "VIN_Hash": ["v1", "v2"],
        "dias_desde_ultimo_servico": [180, 30],
        "gap_com_fallback": [1.4, 0.5],
    })
    original = df.copy()

    resultado = add_risk_explanation(df)

    assert resultado["motivo_risco"].tolist() == [
        "180 dias sem serviço, 40% acima do intervalo esperado do modelo",
        "30 dias sem serviço, 50% abaixo do intervalo esperado do modelo",
    ]
    pd.testing.assert_frame_equal(df, original)


def test_add_risk_explanation_usa_gap_com_fallback_por_padrao_nao_gap_relativo() -> None:
    # VIN de fallback (1 unico servico): gap_relativo fica nulo, mas gap_com_fallback
    # (o que realmente alimenta o score) tem um valor — o motivo deve citar esse.
    df = pd.DataFrame({
        "VIN_Hash": ["v1"],
        "dias_desde_ultimo_servico": [180],
        "gap_relativo": [None],
        "gap_com_fallback": [1.4],
    })

    resultado = add_risk_explanation(df)

    assert resultado["motivo_risco"].iloc[0] == "180 dias sem serviço, 40% acima do intervalo esperado do modelo"


def test_add_risk_explanation_gap_col_e_parametrizavel() -> None:
    df = pd.DataFrame({
        "VIN_Hash": ["v1"],
        "dias_desde_ultimo_servico": [180],
        "gap_relativo": [1.4],
    })

    resultado = add_risk_explanation(df, gap_col="gap_relativo")

    assert resultado["motivo_risco"].iloc[0] == "180 dias sem serviço, 40% acima do intervalo esperado do modelo"
