"""Cálculo de features de veículo a partir das datas de venda/entrega/serviço."""
from __future__ import annotations

import pandas as pd

# Período padrão de garantia: 3 anos a partir de WarrantyStartDate. É o padrão de
# garantia de fábrica mais comum no mercado (ex.: garantia de 3 anos contra defeitos
# de fabricação) — valor de trabalho até o time confirmar/ajustar oficialmente.
WARRANTY_YEARS_PADRAO = 3


def compute_vehicle_age_days(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    sales_date_col: str = "SalesDate",
    delivery_date_col: str = "DeliveryDate",
    output_col: str = "idade_dias",
) -> pd.DataFrame:
    """Calcula a idade do veículo em dias até `reference_date`.

    Usa `sales_date_col` como data de referência principal; quando ela for nula,
    cai para `delivery_date_col`. Ambas as colunas devem já estar como `datetime64`
    (ver `src.infrastructure.xlsx_reader.normalize_date_columns`).

    `df` não é modificado. Se `reference_date` não for informado, usa a data atual
    (normalizada para meia-noite). `idade_dias` fica nulo apenas quando as duas
    datas de origem forem nulas.
    """
    if reference_date is None:
        reference_date = pd.Timestamp.now().normalize()

    result = df.copy()
    data_venda_ou_entrega = result[sales_date_col].fillna(result[delivery_date_col])
    result[output_col] = (reference_date - data_venda_ou_entrega).dt.days

    return result


def compute_median_service_interval_by_model(
    df: pd.DataFrame,
    vin_col: str = "VIN_Hash",
    service_date_col: str = "ServiceDate",
    model_col: str = "ModelName",
) -> pd.DataFrame:
    """Mediana do intervalo (em dias) entre serviços consecutivos do mesmo VIN, por modelo.

    Para cada VIN, ordena os serviços por data e calcula o intervalo entre um serviço e
    o anterior (`diff`). VINs com apenas 1 serviço não geram intervalo (o `diff` da
    primeira linha é nulo) e ficam naturalmente de fora do cálculo — não é preciso
    filtrar por contagem de serviços à parte. Linhas com `service_date_col` nulo são
    ignoradas. `service_date_col` deve já estar como `datetime64`.

    `df` não é modificado. Retorna uma tabela com uma linha por modelo, colunas
    `[model_col, "mediana_dias", "n_intervalos"]`, ordenada por `mediana_dias`.
    """
    dados = df[[vin_col, service_date_col, model_col]].dropna(subset=[service_date_col])
    dados = dados.sort_values([vin_col, service_date_col])

    intervalo_dias = dados.groupby(vin_col)[service_date_col].diff().dt.days
    dados = dados.assign(intervalo_dias=intervalo_dias).dropna(subset=["intervalo_dias"])

    return (
        dados.groupby(model_col)["intervalo_dias"]
        .agg(mediana_dias="median", n_intervalos="count")
        .sort_values("mediana_dias")
        .reset_index()
    )


def compute_days_since_last_service(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    vin_col: str = "VIN_Hash",
    service_date_col: str = "ServiceDate",
    output_col: str = "dias_desde_ultimo_servico",
) -> pd.DataFrame:
    """Por VIN, dias entre o serviço mais recente e `reference_date`.

    Ignora linhas com `service_date_col` nulo. `df` não é modificado. Se
    `reference_date` não for informado, usa a data atual (normalizada para meia-noite).

    Retorna uma linha por VIN, colunas `[vin_col, output_col]`.
    """
    if reference_date is None:
        reference_date = pd.Timestamp.now().normalize()

    ultimo_servico = df.dropna(subset=[service_date_col]).groupby(vin_col)[service_date_col].max()
    dias = (reference_date - ultimo_servico).dt.days

    return dias.rename(output_col).reset_index()


def compute_gap_relativo(
    dias_desde_ultimo_servico: pd.Series, intervalo_mediano_esperado: pd.Series
) -> pd.Series:
    """Gap relativo: dias desde o último serviço ÷ intervalo mediano esperado do modelo.

    É a feature central do modelo de risco de evasão — valores acima de 1 indicam que
    o veículo já passou do intervalo típico de manutenção do seu modelo. Intervalo
    esperado nulo ou igual a 0 produz `gap_relativo` nulo, em vez de erro/infinito.
    """
    denominador = intervalo_mediano_esperado.mask(intervalo_mediano_esperado == 0)
    return (dias_desde_ultimo_servico / denominador).rename("gap_relativo")


def build_gap_relativo_table(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    vin_col: str = "VIN_Hash",
    service_date_col: str = "ServiceDate",
    model_col: str = "ModelName",
) -> pd.DataFrame:
    """Tabela por VIN com `gap_relativo` = dias desde o último serviço ÷ intervalo mediano do modelo.

    Combina `compute_days_since_last_service` e `compute_median_service_interval_by_model`
    (mediana calculada com os dados de todos os VINs de `df`, incluindo o próprio VIN).
    `df` não é modificado.

    Retorna uma linha por VIN, colunas
    `[vin_col, "dias_desde_ultimo_servico", model_col, "intervalo_mediano_esperado", "gap_relativo"]`.
    """
    intervalo_por_modelo = compute_median_service_interval_by_model(
        df, vin_col=vin_col, service_date_col=service_date_col, model_col=model_col
    )[[model_col, "mediana_dias"]].rename(columns={"mediana_dias": "intervalo_mediano_esperado"})

    dias_desde_ultimo = compute_days_since_last_service(
        df, reference_date=reference_date, vin_col=vin_col, service_date_col=service_date_col
    )

    modelo_por_vin = df[[vin_col, model_col]].drop_duplicates(subset=[vin_col])

    resultado = dias_desde_ultimo.merge(modelo_por_vin, on=vin_col, how="left")
    resultado = resultado.merge(intervalo_por_modelo, on=model_col, how="left")
    resultado["gap_relativo"] = compute_gap_relativo(
        resultado["dias_desde_ultimo_servico"], resultado["intervalo_mediano_esperado"]
    )

    return resultado


def compute_service_count_and_gap_std(
    df: pd.DataFrame,
    vin_col: str = "VIN_Hash",
    service_date_col: str = "ServiceDate",
) -> pd.DataFrame:
    """Por VIN: número de serviços (`n_servicos`) e desvio padrão dos intervalos entre
    serviços consecutivos (`desvio_padrao_gaps`).

    `desvio_padrao_gaps` exige pelo menos 2 intervalos (3+ serviços) para não ser nulo —
    isso já sai de graça do `std` amostral (ddof=1) do pandas sobre 0 ou 1 intervalo
    válido, sem precisar filtrar por contagem à parte. Linhas com `service_date_col`
    nulo são ignoradas tanto na contagem quanto no cálculo do desvio.

    `df` não é modificado. Retorna uma linha por VIN, colunas
    `[vin_col, "n_servicos", "desvio_padrao_gaps"]`.
    """
    dados = df.dropna(subset=[service_date_col]).sort_values([vin_col, service_date_col])

    n_servicos = dados.groupby(vin_col)[service_date_col].size().rename("n_servicos")

    intervalo_dias = dados.groupby(vin_col)[service_date_col].diff().dt.days
    desvio_padrao_gaps = intervalo_dias.groupby(dados[vin_col]).std().rename("desvio_padrao_gaps")

    return pd.concat([n_servicos, desvio_padrao_gaps], axis=1).reset_index()


def compute_distinct_dealers_count(
    df: pd.DataFrame,
    vin_col: str = "VIN_Hash",
    dealer_col: str = "DealerCode",
) -> pd.DataFrame:
    """Por VIN, número de concessionárias distintas (`n_dealers_distintos`) usadas no
    histórico de serviços.

    Linhas com `dealer_col` nulo são ignoradas na contagem (`nunique` já descarta NaN
    por padrão). `df` não é modificado.

    Retorna uma linha por VIN, colunas `[vin_col, "n_dealers_distintos"]`.
    """
    return (
        df.groupby(vin_col)[dealer_col]
        .nunique()
        .rename("n_dealers_distintos")
        .reset_index()
    )


def compute_dentro_garantia(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    warranty_start_col: str = "WarrantyStartDate",
    warranty_years: int = WARRANTY_YEARS_PADRAO,
    output_col: str = "dentro_garantia",
) -> pd.DataFrame:
    """Marca se o veículo está dentro da garantia em `reference_date`.

    Fim da garantia = `warranty_start_col` + `warranty_years` anos; o veículo está
    dentro da garantia se `reference_date` for anterior ou igual a essa data. Quando
    `warranty_start_col` é nulo, `dentro_garantia` fica `pd.NA` (garantia desconhecida,
    não "fora da garantia"). `warranty_start_col` deve já estar como `datetime64`.

    `df` não é modificado. Se `reference_date` não for informado, usa a data atual
    (normalizada para meia-noite).
    """
    if reference_date is None:
        reference_date = pd.Timestamp.now().normalize()

    result = df.copy()
    fim_garantia = result[warranty_start_col] + pd.DateOffset(years=warranty_years)

    dentro_garantia = (reference_date <= fim_garantia).astype("boolean")
    dentro_garantia[result[warranty_start_col].isna()] = pd.NA
    result[output_col] = dentro_garantia

    return result
