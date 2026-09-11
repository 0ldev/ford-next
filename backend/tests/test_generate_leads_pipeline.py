import numpy as np
import pandas as pd
import pytest

from src.interfaces.pipeline.generate_leads import LEADS_SCHEMA, build_leads_table, export_leads_csv


class _ModeloFixo:
    """Stub: sempre retorna a mesma probabilidade de risco (0.99), independente da entrada."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.full((len(X), 2), [0.01, 0.99])


def _tabela_features() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": ["v1", "v2", "v3"],
        "ModelName": ["RANGER", "ECOSPORT", "ECOSPORT"],
        "DealerCode": [10, 10, 20],
        # v2: fora de RANGER/KA (heuristica) com idade_dias nula (ex.: sem SalesDate/
        # DeliveryDate) — a heuristica nao usa idade_dias, so gap_com_fallback, entao
        # nao deveria ser descartado do leads.csv por essa coluna faltando.
        "idade_dias": [500.0, None, 500.0],
        "gap_com_fallback": [2.5, 2.5, 0.5],
        "n_servicos": [3, 3, 3],
        "dias_desde_ultimo_servico": [200.0, 200.0, 50.0],
    })


def test_build_leads_table_nao_descarta_vin_de_heuristica_com_idade_nula(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.interfaces.pipeline.generate_leads.load_features", lambda: _tabela_features()
    )
    monkeypatch.setattr(
        "src.interfaces.pipeline.generate_leads.load_model", lambda: _ModeloFixo()
    )

    resultado = build_leads_table().set_index("VIN_Hash")

    assert "v2" in resultado.index
    assert resultado.loc["v2", "score_risco"] == 1.0  # heuristica: gap 2.5 > threshold 2.0


def test_build_leads_table_ainda_descarta_vin_de_ml_com_feature_faltando(monkeypatch) -> None:
    tabela = _tabela_features()
    tabela.loc[tabela["VIN_Hash"] == "v1", "idade_dias"] = None  # v1 e RANGER (ML)

    monkeypatch.setattr("src.interfaces.pipeline.generate_leads.load_features", lambda: tabela)
    monkeypatch.setattr("src.interfaces.pipeline.generate_leads.load_model", lambda: _ModeloFixo())

    resultado = build_leads_table()

    assert "v1" not in resultado["VIN_Hash"].values


def _leads_df() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": ["v1", "v2"],
        "DealerCode": [10, 20],
        "score_risco": [0.9, 0.3],
        "motivo_risco": ["180 dias sem serviço, 40% acima do intervalo esperado do modelo", "dentro do prazo"],
        "ModelName": ["RANGER", "KA"],
        "dias_desde_ultimo_servico": [180.0, 30.0],
        "coluna_extra_que_nao_faz_parte_do_schema": ["x", "y"],
    })


def test_export_gera_exatamente_as_colunas_do_schema_na_ordem_certa(tmp_path) -> None:
    destino = export_leads_csv(_leads_df(), path=tmp_path / "leads.csv")

    resultado = pd.read_csv(destino)
    assert resultado.columns.tolist() == list(LEADS_SCHEMA.values())


def test_export_renomeia_as_colunas_conforme_o_schema(tmp_path) -> None:
    destino = export_leads_csv(_leads_df(), path=tmp_path / "leads.csv")

    resultado = pd.read_csv(destino)
    assert resultado["vin"].tolist() == ["v1", "v2"]
    assert resultado["dealerCode"].tolist() == [10, 20]
    assert resultado["score"].tolist() == [0.9, 0.3]
    assert resultado["modelo"].tolist() == ["RANGER", "KA"]
    assert resultado["diasSemServico"].tolist() == [180.0, 30.0]


def test_export_nao_inclui_colunas_fora_do_schema(tmp_path) -> None:
    destino = export_leads_csv(_leads_df(), path=tmp_path / "leads.csv")

    resultado = pd.read_csv(destino)
    assert "coluna_extra_que_nao_faz_parte_do_schema" not in resultado.columns


def test_export_cria_diretorio_de_destino_se_nao_existir(tmp_path) -> None:
    destino = export_leads_csv(_leads_df(), path=tmp_path / "subpasta" / "leads.csv")
    assert destino.exists()


def test_export_levanta_erro_claro_quando_falta_coluna_do_schema(tmp_path) -> None:
    df_incompleto = _leads_df().drop(columns=["DealerCode"])

    with pytest.raises(KeyError, match="DealerCode"):
        export_leads_csv(df_incompleto, path=tmp_path / "leads.csv")


def test_export_nao_modifica_o_dataframe_original(tmp_path) -> None:
    df = _leads_df()
    original = df.copy()

    export_leads_csv(df, path=tmp_path / "leads.csv")

    pd.testing.assert_frame_equal(df, original)
