"""Cálculo do indicador de VIN share (retorno de veículos à rede) com filtros cruzados."""
from __future__ import annotations

from typing import Literal

import pandas as pd

from src.application.build_vehicle_features import compute_vehicle_age_days

FaixaIdade = Literal["0-1", "1-2", "2-4", "4+"]

# Mesmas faixas do catálogo combinado com o front-end
# (frontend/src/infrastructure/mockData.ts::FAIXAS_IDADE). "4+" não tem limite superior.
_DIAS_POR_ANO = 365.25
LIMITES_FAIXA_IDADE: dict[str, tuple[float, float]] = {
    "0-1": (0.0, 1 * _DIAS_POR_ANO),
    "1-2": (1 * _DIAS_POR_ANO, 2 * _DIAS_POR_ANO),
    "2-4": (2 * _DIAS_POR_ANO, 4 * _DIAS_POR_ANO),
    "4+": (4 * _DIAS_POR_ANO, float("inf")),
}


def compute_vin_share(
    df: pd.DataFrame,
    concessionaria: str | None = None,
    modelo: str | None = None,
    faixa_idade: FaixaIdade | None = None,
    tipo_servico: str | None = None,
    periodo_inicio: pd.Timestamp | None = None,
    periodo_fim: pd.Timestamp | None = None,
    vin_col: str = "VIN_Hash",
    dealer_col: str = "DealerCode",
    model_col: str = "ModelName",
    service_type_col: str = "ServiceType",
    service_date_col: str = "ServiceDate",
) -> dict[str, float | int]:
    """VIN share: % de veículos elegíveis que retornaram à rede sob os filtros informados.

    `df` é o histórico de serviços (uma linha por ordem de serviço, várias por VIN),
    com as colunas de data já em `datetime64` (ver `vin_share_repository.load_vin_share_data`).

    População elegível (denominador): VINs distintos que casam com `modelo` e
    `faixa_idade` — a idade é calculada em `periodo_fim` (ou hoje, se não informado),
    igual a `build_vehicle_features.compute_vehicle_age_days`. Se `concessionaria` for
    informada, o denominador também é restrito aos VINs que já tiveram ao menos uma
    ordem de serviço naquela concessionária (o "fluxo" daquele dealer) — não é possível
    saber, só com este dataset, em qual concessionária o veículo foi vendido.

    "Com serviço" (numerador): subconjunto dos elegíveis que teve ao menos uma ordem de
    serviço casando também com `concessionaria` (se informada), `tipo_servico` e o
    intervalo `[periodo_inicio, periodo_fim]` — isto é, o "retorno" propriamente dito,
    dentro dos filtros que descrevem o evento de serviço (não o veículo).

    `vinShareEstimado` é 0.0 (não erro/NaN/inf) quando não há veículo elegível.

    Linhas com `service_date_col` nulo são descartadas logo de início — sem uma data de
    serviço válida não há "ordem de serviço" de verdade, nem para contar no numerador
    nem para estabelecer o vínculo do VIN com uma concessionária.

    Nota sobre a leitura do resultado: como a população elegível é derivada do próprio
    histórico de serviços (não existe, nesta base, uma lista independente de "veículos
    vendidos"), todo VIN nela já foi atendido pela rede alguma vez — sem um filtro de
    `tipo_servico` e/ou período, `vinShareEstimado` tende a 100%. O indicador só fica
    informativo quando usado com período (e/ou tipo de serviço), medindo quantos dos
    elegíveis retornaram dentro daquela janela.
    """
    df = df.dropna(subset=[service_date_col])
    reference_date = periodo_fim if periodo_fim is not None else pd.Timestamp.now().normalize()

    primeira_linha_por_vin = df.groupby(vin_col, as_index=False)[
        ["SalesDate", "DeliveryDate", model_col]
    ].first()
    idade = compute_vehicle_age_days(primeira_linha_por_vin, reference_date=reference_date)

    veiculos = idade.set_index(vin_col)[["idade_dias", model_col]]

    if modelo is not None:
        veiculos = veiculos[veiculos[model_col] == modelo]

    if faixa_idade is not None:
        minimo, maximo = LIMITES_FAIXA_IDADE[faixa_idade]
        veiculos = veiculos[(veiculos["idade_dias"] >= minimo) & (veiculos["idade_dias"] < maximo)]

    if concessionaria is not None:
        vins_do_dealer = df.loc[df[dealer_col].astype(str) == concessionaria, vin_col].unique()
        veiculos = veiculos[veiculos.index.isin(vins_do_dealer)]

    total_elegiveis = len(veiculos)

    servicos = df[df[vin_col].isin(veiculos.index)]
    if concessionaria is not None:
        servicos = servicos[servicos[dealer_col].astype(str) == concessionaria]
    if tipo_servico is not None:
        servicos = servicos[servicos[service_type_col] == tipo_servico]
    if periodo_inicio is not None:
        servicos = servicos[servicos[service_date_col] >= periodo_inicio]
    if periodo_fim is not None:
        servicos = servicos[servicos[service_date_col] <= periodo_fim]

    total_com_servico = int(servicos[vin_col].nunique())

    vin_share_estimado = (total_com_servico / total_elegiveis * 100) if total_elegiveis else 0.0

    return {
        "vinShareEstimado": round(vin_share_estimado, 1),
        "totalVeiculosElegiveis": int(total_elegiveis),
        "totalComServico": total_com_servico,
    }
