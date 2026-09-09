import pandas as pd
import pytest

from src.infrastructure.xlsx_reader import (
    DATE_COLUMNS,
    normalize_date_columns,
    read_xlsx,
    remove_duplicate_service_orders,
)


@pytest.fixture
def df_datas_mistas() -> pd.DataFrame:
    return pd.DataFrame({
        "ServiceDate": ["10/07/2023", "não é uma data", None, "13/13/2023"],
        "SalesDate": ["4/17/2023", "4/17/2023", "4/17/2023", "4/17/2023"],
        "DeliveryDate": ["4/28/2023", "", "4/28/2023", "lixo"],
        "WarrantyStartDate": ["4/28/2023", "4/28/2023", None, "4/28/2023"],
        "VIN_Hash": ["a", "b", "c", "d"],
    })


def test_datas_validas_sao_convertidas_para_datetime(df_datas_mistas: pd.DataFrame) -> None:
    result, _ = normalize_date_columns(df_datas_mistas)

    for column in DATE_COLUMNS:
        assert pd.api.types.is_datetime64_any_dtype(result[column])

    assert result["SalesDate"].iloc[0] == pd.Timestamp("2023-04-17")


def test_valores_mal_formatados_viram_nat_sem_quebrar(df_datas_mistas: pd.DataFrame) -> None:
    result, _ = normalize_date_columns(df_datas_mistas)

    assert pd.isna(result["ServiceDate"].iloc[1])  # "não é uma data"
    assert pd.isna(result["ServiceDate"].iloc[3])  # "13/13/2023" (mês inválido)
    assert pd.isna(result["DeliveryDate"].iloc[3])  # "lixo"


def test_valores_nulos_sao_preservados_como_nat(df_datas_mistas: pd.DataFrame) -> None:
    result, _ = normalize_date_columns(df_datas_mistas)

    assert pd.isna(result["ServiceDate"].iloc[2])  # None
    assert pd.isna(result["WarrantyStartDate"].iloc[2])  # None


def test_relatorio_conta_nulos_e_invalidos_por_coluna(df_datas_mistas: pd.DataFrame) -> None:
    _, report = normalize_date_columns(df_datas_mistas)

    assert report == {
        "ServiceDate": 3,  # "não é uma data" + None + "13/13/2023"
        "SalesDate": 0,
        "DeliveryDate": 2,  # "" + "lixo"
        "WarrantyStartDate": 1,  # None
    }


def test_dataframe_original_nao_e_modificado(df_datas_mistas: pd.DataFrame) -> None:
    original = df_datas_mistas.copy()
    normalize_date_columns(df_datas_mistas)

    pd.testing.assert_frame_equal(df_datas_mistas, original)


def test_read_xlsx_le_arquivo_e_normaliza_datas(tmp_path) -> None:
    xlsx_path = tmp_path / "vendas.xlsx"
    df = pd.DataFrame({
        "VIN_Hash": ["a", "b"],
        "ServiceType": ["Maintenance", "Repair"],
        "ServiceDate": ["10/07/2023", "data invalida"],
        "SalesDate": ["4/17/2023", None],
        "DeliveryDate": ["4/28/2023", "4/28/2023"],
        "WarrantyStartDate": ["4/28/2023", "4/28/2023"],
    })
    df.to_excel(xlsx_path, index=False)

    result, date_report, n_duplicates_removed = read_xlsx(xlsx_path)

    assert pd.api.types.is_datetime64_any_dtype(result["ServiceDate"])
    assert date_report == {
        "ServiceDate": 1,
        "SalesDate": 1,
        "DeliveryDate": 0,
        "WarrantyStartDate": 0,
    }
    assert n_duplicates_removed == 0


class TestRemoveDuplicateServiceOrders:
    @pytest.fixture
    def df_com_duplicatas(self) -> pd.DataFrame:
        return pd.DataFrame({
            "VIN_Hash": ["vin1", "vin1", "vin1", "vin1", "vin2"],
            "ServiceDate": pd.to_datetime([
                "2023-04-17", "2023-04-17", "2023-04-17", "2023-05-01", "2023-04-17",
            ]),
            "ServiceType": ["Maintenance", "Maintenance", "Repair", "Maintenance", "Maintenance"],
            "ServiceOrder": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

    def test_linha_duplicada_e_removida_mantendo_a_primeira(self, df_com_duplicatas: pd.DataFrame) -> None:
        result, _ = remove_duplicate_service_orders(df_com_duplicatas)

        assert len(result) == 4
        # a linha 0 (ServiceOrder=1.0) foi mantida, a linha 1 (duplicata, ServiceOrder=2.0) removida
        assert result["ServiceOrder"].tolist() == [1.0, 3.0, 4.0, 5.0]

    def test_mesmo_vin_data_diferente_nao_e_duplicata(self, df_com_duplicatas: pd.DataFrame) -> None:
        result, _ = remove_duplicate_service_orders(df_com_duplicatas)

        assert 4.0 in result["ServiceOrder"].tolist()  # vin1 em 2023-05-01, data diferente

    def test_mesmo_vin_mesma_data_tipo_diferente_nao_e_duplicata(self, df_com_duplicatas: pd.DataFrame) -> None:
        result, _ = remove_duplicate_service_orders(df_com_duplicatas)

        assert 3.0 in result["ServiceOrder"].tolist()  # vin1 em 2023-04-17, mas Repair (não Maintenance)

    def test_conta_quantas_linhas_foram_removidas(self, df_com_duplicatas: pd.DataFrame) -> None:
        _, n_removed = remove_duplicate_service_orders(df_com_duplicatas)

        assert n_removed == 1

    def test_sem_duplicatas_nao_remove_nada(self) -> None:
        df = pd.DataFrame({
            "VIN_Hash": ["vin1", "vin2"],
            "ServiceDate": pd.to_datetime(["2023-04-17", "2023-04-17"]),
            "ServiceType": ["Maintenance", "Maintenance"],
        })

        result, n_removed = remove_duplicate_service_orders(df)

        assert n_removed == 0
        assert len(result) == 2

    def test_dataframe_original_nao_e_modificado(self, df_com_duplicatas: pd.DataFrame) -> None:
        original = df_com_duplicatas.copy()
        remove_duplicate_service_orders(df_com_duplicatas)

        pd.testing.assert_frame_equal(df_com_duplicatas, original)
