import pandas as pd
import pytest

from src.interfaces.pipeline.generate_leads import LEADS_SCHEMA, export_leads_csv


def _leads_df() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": ["v1", "v2"],
        "DealerCode": [10, 20],
        "score_risco": [0.9, 0.3],
        "motivo_risco": ["180 dias sem serviço, 40% acima do intervalo esperado do modelo", "dentro do prazo"],
        "ModelName": ["RANGER", "KA"],
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
