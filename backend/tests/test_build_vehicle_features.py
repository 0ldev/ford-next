import pandas as pd
import pytest

from src.application.build_vehicle_features import (
    build_gap_relativo_table,
    compute_days_since_last_service,
    compute_dentro_garantia,
    compute_distinct_dealers_count,
    compute_gap_relativo,
    compute_median_service_interval_by_model,
    compute_service_count_and_gap_std,
    compute_vehicle_age_days,
)

REFERENCE_DATE = pd.Timestamp("2024-01-31")


def test_usa_sales_date_quando_disponivel() -> None:
    df = pd.DataFrame({
        "SalesDate": pd.to_datetime(["2024-01-01"]),
        "DeliveryDate": pd.to_datetime(["2024-01-10"]),
    })

    result = compute_vehicle_age_days(df, reference_date=REFERENCE_DATE)

    assert result["idade_dias"].iloc[0] == 30  # 2024-01-01 -> 2024-01-31


def test_usa_delivery_date_como_fallback_quando_sales_date_nulo() -> None:
    df = pd.DataFrame({
        "SalesDate": pd.to_datetime([None]),
        "DeliveryDate": pd.to_datetime(["2024-01-21"]),
    })

    result = compute_vehicle_age_days(df, reference_date=REFERENCE_DATE)

    assert result["idade_dias"].iloc[0] == 10  # 2024-01-21 -> 2024-01-31


def test_nulo_quando_ambas_as_datas_sao_nulas() -> None:
    df = pd.DataFrame({
        "SalesDate": pd.to_datetime([None]),
        "DeliveryDate": pd.to_datetime([None]),
    })

    result = compute_vehicle_age_days(df, reference_date=REFERENCE_DATE)

    assert pd.isna(result["idade_dias"].iloc[0])


def test_calcula_para_multiplos_vins_de_uma_vez() -> None:
    df = pd.DataFrame({
        "VIN_Hash": ["v1", "v2", "v3"],
        "SalesDate": pd.to_datetime(["2024-01-01", None, "2024-01-30"]),
        "DeliveryDate": pd.to_datetime(["2024-01-05", "2024-01-11", "2024-01-31"]),
    })

    result = compute_vehicle_age_days(df, reference_date=REFERENCE_DATE)

    assert result["idade_dias"].tolist() == [30, 20, 1]


def test_dataframe_original_nao_e_modificado() -> None:
    df = pd.DataFrame({
        "SalesDate": pd.to_datetime(["2024-01-01"]),
        "DeliveryDate": pd.to_datetime(["2024-01-10"]),
    })
    original = df.copy()

    compute_vehicle_age_days(df, reference_date=REFERENCE_DATE)

    pd.testing.assert_frame_equal(df, original)


def test_reference_date_padrao_e_a_data_atual() -> None:
    dez_dias_atras = pd.Timestamp.now().normalize() - pd.Timedelta(days=10)
    df = pd.DataFrame({
        "SalesDate": [dez_dias_atras],
        "DeliveryDate": pd.to_datetime([None]),
    })

    result = compute_vehicle_age_days(df)

    assert result["idade_dias"].iloc[0] == 10


def _servicos_df() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": [
            "vA", "vA", "vA",  # modelo X: intervalos 10, 20
            "vB", "vB",  # modelo X: intervalo 5
            "vC",  # modelo Y: servico unico, nao gera intervalo
            "vD", "vD",  # modelo Y: intervalo 100
        ],
        "ServiceDate": pd.to_datetime([
            "2024-01-01", "2024-01-11", "2024-01-31",
            "2024-02-01", "2024-02-06",
            "2024-03-01",
            "2024-01-01", "2024-04-10",
        ]),
        "ModelName": ["X", "X", "X", "X", "X", "Y", "Y", "Y"],
    })


def test_calcula_mediana_do_intervalo_por_modelo() -> None:
    resultado = compute_median_service_interval_by_model(_servicos_df())

    linha_x = resultado.set_index("ModelName").loc["X"]
    linha_y = resultado.set_index("ModelName").loc["Y"]

    assert linha_x["mediana_dias"] == 10  # mediana de [10, 20, 5]
    assert linha_x["n_intervalos"] == 3
    assert linha_y["mediana_dias"] == 100  # unico intervalo do modelo Y
    assert linha_y["n_intervalos"] == 1


def test_vin_com_servico_unico_nao_gera_intervalo() -> None:
    resultado = compute_median_service_interval_by_model(_servicos_df())

    # vC (modelo Y, 1 servico) nao deveria contribuir: modelo Y so tem 1 intervalo (de vD)
    assert resultado.set_index("ModelName").loc["Y", "n_intervalos"] == 1


def test_resultado_ordenado_por_mediana_dias() -> None:
    resultado = compute_median_service_interval_by_model(_servicos_df())

    assert resultado["mediana_dias"].is_monotonic_increasing


def test_linhas_com_data_de_servico_nula_sao_ignoradas() -> None:
    df = _servicos_df()
    df = pd.concat([df, pd.DataFrame({
        "VIN_Hash": ["vE"],
        "ServiceDate": [pd.NaT],
        "ModelName": ["X"],
    })], ignore_index=True)

    resultado_com_nulo = compute_median_service_interval_by_model(df)
    resultado_sem_nulo = compute_median_service_interval_by_model(_servicos_df())

    pd.testing.assert_frame_equal(resultado_com_nulo, resultado_sem_nulo)


def test_dataframe_original_nao_e_modificado_no_intervalo_por_modelo() -> None:
    df = _servicos_df()
    original = df.copy()

    compute_median_service_interval_by_model(df)

    pd.testing.assert_frame_equal(df, original)


def test_dias_desde_ultimo_servico_usa_o_servico_mais_recente_por_vin() -> None:
    resultado = compute_days_since_last_service(_servicos_df(), reference_date=pd.Timestamp("2024-05-01"))
    resultado = resultado.set_index("VIN_Hash")

    assert resultado.loc["vA", "dias_desde_ultimo_servico"] == 91  # ultimo servico 2024-01-31
    assert resultado.loc["vB", "dias_desde_ultimo_servico"] == 85  # ultimo servico 2024-02-06
    assert resultado.loc["vD", "dias_desde_ultimo_servico"] == 21  # ultimo servico 2024-04-10


def test_compute_gap_relativo_e_a_razao_entre_as_duas_series() -> None:
    dias = pd.Series([91.0, 61.0])
    intervalo = pd.Series([10.0, 100.0])

    gap = compute_gap_relativo(dias, intervalo)

    assert gap.tolist() == [9.1, 0.61]


def test_compute_gap_relativo_e_nulo_quando_intervalo_esperado_e_zero_ou_nulo() -> None:
    dias = pd.Series([91.0, 61.0, 30.0])
    intervalo = pd.Series([0.0, None, 10.0])

    gap = compute_gap_relativo(dias, intervalo)

    assert pd.isna(gap.iloc[0])
    assert pd.isna(gap.iloc[1])
    assert gap.iloc[2] == 3.0


def test_build_gap_relativo_table_combina_dias_e_intervalo_por_modelo() -> None:
    resultado = build_gap_relativo_table(_servicos_df(), reference_date=pd.Timestamp("2024-05-01"))
    resultado = resultado.set_index("VIN_Hash")

    # modelo X: mediana=10 (de vA/vB); modelo Y: mediana=100 (so vD gera intervalo)
    assert resultado.loc["vA", "gap_relativo"] == pytest.approx(91 / 10)
    assert resultado.loc["vB", "gap_relativo"] == pytest.approx(85 / 10)
    assert resultado.loc["vD", "gap_relativo"] == pytest.approx(21 / 100)


def test_build_gap_relativo_table_nao_modifica_o_original() -> None:
    df = _servicos_df()
    original = df.copy()

    build_gap_relativo_table(df, reference_date=pd.Timestamp("2024-05-01"))

    pd.testing.assert_frame_equal(df, original)


def _servicos_contagem_df() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": [
            "vA", "vA", "vA", "vA",  # 4 servicos, intervalos [10, 20, 30]
            "vB", "vB",  # 2 servicos, 1 intervalo (nao atinge 3+ servicos)
            "vC",  # 1 servico, 0 intervalos
            "vD", "vD", "vD",  # 3 servicos, intervalos [5, 15] (minimo p/ desvio)
        ],
        "ServiceDate": pd.to_datetime([
            "2024-01-01", "2024-01-11", "2024-01-31", "2024-03-01",
            "2024-02-01", "2024-02-06",
            "2024-03-01",
            "2024-01-01", "2024-01-06", "2024-01-21",
        ]),
    })


def test_conta_numero_de_servicos_por_vin() -> None:
    resultado = compute_service_count_and_gap_std(_servicos_contagem_df()).set_index("VIN_Hash")

    assert resultado.loc["vA", "n_servicos"] == 4
    assert resultado.loc["vB", "n_servicos"] == 2
    assert resultado.loc["vC", "n_servicos"] == 1
    assert resultado.loc["vD", "n_servicos"] == 3


def test_desvio_padrao_gaps_calculado_para_3_ou_mais_servicos() -> None:
    resultado = compute_service_count_and_gap_std(_servicos_contagem_df()).set_index("VIN_Hash")

    assert resultado.loc["vA", "desvio_padrao_gaps"] == pytest.approx(10.0)  # std([10,20,30])
    assert resultado.loc["vD", "desvio_padrao_gaps"] == pytest.approx(7.0710678118654755)  # std([5,15])


def test_desvio_padrao_gaps_e_nulo_com_menos_de_3_servicos() -> None:
    resultado = compute_service_count_and_gap_std(_servicos_contagem_df()).set_index("VIN_Hash")

    assert pd.isna(resultado.loc["vB", "desvio_padrao_gaps"])  # 2 servicos, so 1 intervalo
    assert pd.isna(resultado.loc["vC", "desvio_padrao_gaps"])  # 1 servico, 0 intervalos


def test_service_count_and_gap_std_nao_modifica_o_original() -> None:
    df = _servicos_contagem_df()
    original = df.copy()

    compute_service_count_and_gap_std(df)

    pd.testing.assert_frame_equal(df, original)


def _servicos_dealers_df() -> pd.DataFrame:
    return pd.DataFrame({
        "VIN_Hash": ["vA", "vA", "vA", "vB", "vB", "vC", "vD", "vD"],
        "DealerCode": [1, 1, 2, 5, 5, 9, 3, None],
    })


def test_conta_dealers_distintos_por_vin() -> None:
    resultado = compute_distinct_dealers_count(_servicos_dealers_df()).set_index("VIN_Hash")

    assert resultado.loc["vA", "n_dealers_distintos"] == 2  # dealers 1 e 2
    assert resultado.loc["vB", "n_dealers_distintos"] == 1  # sempre o dealer 5
    assert resultado.loc["vC", "n_dealers_distintos"] == 1


def test_dealer_nulo_e_ignorado_na_contagem() -> None:
    resultado = compute_distinct_dealers_count(_servicos_dealers_df()).set_index("VIN_Hash")

    assert resultado.loc["vD", "n_dealers_distintos"] == 1  # so o dealer 3 conta; None e ignorado


def test_distinct_dealers_count_nao_modifica_o_original() -> None:
    df = _servicos_dealers_df()
    original = df.copy()

    compute_distinct_dealers_count(df)

    pd.testing.assert_frame_equal(df, original)


def _garantia_df() -> pd.DataFrame:
    return pd.DataFrame({
        "WarrantyStartDate": pd.to_datetime(["2021-01-01", "2021-01-01", "2021-01-01", None]),
    })
    # fim da garantia (3 anos) = 2024-01-01 para as 3 primeiras linhas


def test_dentro_do_prazo_e_true() -> None:
    resultado = compute_dentro_garantia(_garantia_df(), reference_date=pd.Timestamp("2023-06-01"))
    assert resultado["dentro_garantia"].iloc[0] == True  # noqa: E712


def test_exatamente_no_limite_e_true() -> None:
    resultado = compute_dentro_garantia(_garantia_df(), reference_date=pd.Timestamp("2024-01-01"))
    assert resultado["dentro_garantia"].iloc[1] == True  # noqa: E712


def test_apos_o_limite_e_false() -> None:
    resultado = compute_dentro_garantia(_garantia_df(), reference_date=pd.Timestamp("2024-01-02"))
    assert resultado["dentro_garantia"].iloc[2] == False  # noqa: E712


def test_warranty_start_nulo_gera_na_nao_false() -> None:
    resultado = compute_dentro_garantia(_garantia_df(), reference_date=pd.Timestamp("2023-06-01"))
    assert resultado["dentro_garantia"].iloc[3] is pd.NA


def test_warranty_years_e_parametrizavel() -> None:
    resultado = compute_dentro_garantia(
        _garantia_df(), reference_date=pd.Timestamp("2022-06-01"), warranty_years=1
    )
    assert resultado["dentro_garantia"].iloc[0] == False  # noqa: E712 (garantia de 1 ano ja expirou em 2022-01-01)


def test_dentro_garantia_nao_modifica_o_original() -> None:
    df = _garantia_df()
    original = df.copy()

    compute_dentro_garantia(df, reference_date=pd.Timestamp("2023-06-01"))

    pd.testing.assert_frame_equal(df, original)
