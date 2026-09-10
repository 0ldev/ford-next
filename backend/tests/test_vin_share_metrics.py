import pandas as pd
import pytest

from src.application.vin_share_metrics import compute_vin_share


def _historico() -> pd.DataFrame:
    hoje = pd.Timestamp.now().normalize()

    def dias_atras(dias: int) -> pd.Timestamp:
        return hoje - pd.Timedelta(days=dias)

    linhas = [
        # v1: RANGER, ~6 meses, 2 servicos (dealer 100 ha 30d, dealer 200 ha 5d)
        {
            "VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 100,
            "ServiceType": "Manutencao", "ServiceDate": dias_atras(30),
            "SalesDate": dias_atras(180), "DeliveryDate": dias_atras(180),
        },
        {
            "VIN_Hash": "v1", "ModelName": "RANGER", "DealerCode": 200,
            "ServiceType": "Manutencao", "ServiceDate": dias_atras(5),
            "SalesDate": dias_atras(180), "DeliveryDate": dias_atras(180),
        },
        # v2: RANGER, ~6 anos (faixa 4+), Recall no dealer 200 ha 400 dias
        {
            "VIN_Hash": "v2", "ModelName": "RANGER", "DealerCode": 200,
            "ServiceType": "Recall", "ServiceDate": dias_atras(400),
            "SalesDate": dias_atras(2200), "DeliveryDate": dias_atras(2200),
        },
        # v3: KA, ~5 meses, Manutencao no dealer 200 ha 10 dias
        {
            "VIN_Hash": "v3", "ModelName": "KA", "DealerCode": 200,
            "ServiceType": "Manutencao", "ServiceDate": dias_atras(10),
            "SalesDate": dias_atras(150), "DeliveryDate": dias_atras(150),
        },
        # v4: RANGER, ~5 meses, Recall no dealer 100 ha 500 dias (fora da janela dos testes de periodo)
        {
            "VIN_Hash": "v4", "ModelName": "RANGER", "DealerCode": 100,
            "ServiceType": "Recall", "ServiceDate": dias_atras(500),
            "SalesDate": dias_atras(160), "DeliveryDate": dias_atras(160),
        },
    ]
    return pd.DataFrame(linhas)


def test_sem_filtros_vin_share_tende_a_100_por_cento() -> None:
    # Sem tipo_servico/periodo, a populacao elegivel e' derivada do proprio historico
    # de servicos: todo VIN nela ja foi atendido alguma vez (limitacao documentada em
    # compute_vin_share). Por isso 4/4, nao um valor "realista" de mercado.
    resultado = compute_vin_share(_historico())

    assert resultado["totalVeiculosElegiveis"] == 4  # v1, v2, v3, v4
    assert resultado["totalComServico"] == 4
    assert resultado["vinShareEstimado"] == pytest.approx(100.0)


def test_filtro_modelo_restringe_populacao_elegivel() -> None:
    resultado = compute_vin_share(_historico(), modelo="RANGER")

    assert resultado["totalVeiculosElegiveis"] == 3  # v1, v2, v4 (v3 e' KA)
    assert resultado["totalComServico"] == 3


def test_filtro_faixa_idade_0_1_pega_veiculos_recentes() -> None:
    resultado = compute_vin_share(_historico(), faixa_idade="0-1")

    assert resultado["totalVeiculosElegiveis"] == 3  # v1, v3, v4 (~5-6 meses)
    assert resultado["totalComServico"] == 3


def test_filtro_faixa_idade_4_mais_pega_veiculo_antigo() -> None:
    resultado = compute_vin_share(_historico(), faixa_idade="4+")

    assert resultado["totalVeiculosElegiveis"] == 1  # v2 (~6 anos)
    assert resultado["totalComServico"] == 1


def test_filtro_tipo_servico_restringe_so_o_numerador() -> None:
    resultado = compute_vin_share(_historico(), tipo_servico="Recall")

    assert resultado["totalVeiculosElegiveis"] == 4  # nao muda: e' filtro do evento, nao do veiculo
    assert resultado["totalComServico"] == 2  # v2 e v4, unicos com Recall
    assert resultado["vinShareEstimado"] == pytest.approx(50.0)


def test_filtro_periodo_restringe_so_o_numerador() -> None:
    hoje = pd.Timestamp.now().normalize()
    resultado = compute_vin_share(
        _historico(),
        periodo_inicio=hoje - pd.Timedelta(days=60),
        periodo_fim=hoje,
    )

    assert resultado["totalVeiculosElegiveis"] == 4
    assert resultado["totalComServico"] == 2  # v1 (30d/5d) e v3 (10d); v2 (400d) e v4 (500d) ficam de fora
    assert resultado["vinShareEstimado"] == pytest.approx(50.0)


def test_filtro_concessionaria_restringe_elegiveis_ao_historico_do_dealer() -> None:
    # Elegivel = ja teve pelo menos 1 servico no dealer 100 -> v1 (tem 1 dos 2 la) e v4.
    # v2 e v3 nunca passaram pelo dealer 100 -> ficam de fora do denominador tambem.
    resultado = compute_vin_share(_historico(), concessionaria="100")

    assert resultado["totalVeiculosElegiveis"] == 2  # v1, v4
    assert resultado["totalComServico"] == 2  # ambos tem pelo menos 1 servico la


def test_concessionaria_e_periodo_combinados_mostram_gap_entre_elegivel_e_com_servico() -> None:
    hoje = pd.Timestamp.now().normalize()
    resultado = compute_vin_share(
        _historico(),
        concessionaria="100",
        periodo_inicio=hoje - pd.Timedelta(days=60),
        periodo_fim=hoje,
    )

    # elegiveis: mesmo denominador do teste anterior (nao depende de periodo)
    assert resultado["totalVeiculosElegiveis"] == 2  # v1, v4
    # com servico: so v1 tem visita ao dealer 100 dentro dos ultimos 60 dias (30d atras);
    # a visita de v4 ao dealer 100 foi ha 500 dias, fora da janela.
    assert resultado["totalComServico"] == 1
    assert resultado["vinShareEstimado"] == pytest.approx(50.0)


def test_modelo_e_tipo_servico_combinados() -> None:
    resultado = compute_vin_share(_historico(), modelo="RANGER", tipo_servico="Recall")

    assert resultado["totalVeiculosElegiveis"] == 3  # v1, v2, v4
    assert resultado["totalComServico"] == 2  # v2 e v4 tem Recall; v1 so tem Manutencao


def test_sem_veiculo_elegivel_retorna_zero_sem_erro() -> None:
    resultado = compute_vin_share(_historico(), modelo="MODELO_INEXISTENTE")

    assert resultado["totalVeiculosElegiveis"] == 0
    assert resultado["totalComServico"] == 0
    assert resultado["vinShareEstimado"] == 0.0


def test_faixa_idade_invalida_levanta_key_error() -> None:
    with pytest.raises(KeyError):
        compute_vin_share(_historico(), faixa_idade="9+")


def test_linhas_sem_service_date_sao_descartadas() -> None:
    historico = _historico()
    lixo = pd.DataFrame([{
        "VIN_Hash": "v5", "ModelName": "RANGER", "DealerCode": 300,
        "ServiceType": None, "ServiceDate": pd.NaT,
        "SalesDate": pd.Timestamp.now().normalize(), "DeliveryDate": pd.Timestamp.now().normalize(),
    }])
    resultado = compute_vin_share(pd.concat([historico, lixo], ignore_index=True))

    assert resultado["totalVeiculosElegiveis"] == 4  # v5 nao entra: nenhum servico valido
    assert resultado["totalComServico"] == 4


# --------------------------------------------------------------------------- #
# Robustez / casos de borda que nao devem derrubar o endpoint                  #
# --------------------------------------------------------------------------- #

def test_dataframe_vazio_nao_quebra() -> None:
    vazio = _historico().iloc[0:0]

    resultado = compute_vin_share(vazio)

    assert resultado == {"vinShareEstimado": 0.0, "totalVeiculosElegiveis": 0, "totalComServico": 0}


def test_sales_date_e_delivery_date_nulas_nao_quebra() -> None:
    historico = _historico()
    idade_desconhecida = pd.DataFrame([{
        "VIN_Hash": "v6", "ModelName": "RANGER", "DealerCode": 100,
        "ServiceType": "Manutencao", "ServiceDate": pd.Timestamp.now().normalize() - pd.Timedelta(days=5),
        "SalesDate": pd.NaT, "DeliveryDate": pd.NaT,
    }])
    combinado = pd.concat([historico, idade_desconhecida], ignore_index=True)

    # sem filtro de idade: v6 continua elegivel (idade desconhecida nao e' motivo de exclusao)
    resultado = compute_vin_share(combinado)
    assert resultado["totalVeiculosElegiveis"] == 5
    assert resultado["totalComServico"] == 5

    # com filtro de faixa etaria: v6 (idade NaN) nao entra em nenhuma faixa, mas nao quebra
    resultado_faixa = compute_vin_share(combinado, faixa_idade="0-1")
    assert resultado_faixa["totalVeiculosElegiveis"] == 3  # v1, v3, v4 — v6 fica de fora


def test_service_type_nulo_nao_conta_no_filtro_de_tipo_servico() -> None:
    historico = _historico()
    tipo_nulo = pd.DataFrame([{
        "VIN_Hash": "v7", "ModelName": "RANGER", "DealerCode": 100,
        "ServiceType": None, "ServiceDate": pd.Timestamp.now().normalize() - pd.Timedelta(days=1),
        "SalesDate": pd.Timestamp.now().normalize() - pd.Timedelta(days=200),
        "DeliveryDate": pd.Timestamp.now().normalize() - pd.Timedelta(days=200),
    }])
    combinado = pd.concat([historico, tipo_nulo], ignore_index=True)

    resultado = compute_vin_share(combinado, tipo_servico="Manutencao")

    assert resultado["totalVeiculosElegiveis"] == 5  # v7 e' elegivel (tem servico com data valida)
    assert resultado["totalComServico"] == 2  # v1 e v3; v7 (tipo nulo) nao casa com "Manutencao"


def test_periodo_invertido_nao_quebra_so_zera_o_numerador() -> None:
    hoje = pd.Timestamp.now().normalize()
    resultado = compute_vin_share(
        _historico(),
        periodo_inicio=hoje,
        periodo_fim=hoje - pd.Timedelta(days=60),
    )

    assert resultado["totalVeiculosElegiveis"] == 4
    assert resultado["totalComServico"] == 0
    assert resultado["vinShareEstimado"] == 0.0


def test_concessionaria_sem_correspondencia_retorna_zero_sem_erro() -> None:
    resultado = compute_vin_share(_historico(), concessionaria="999999")

    assert resultado["totalVeiculosElegiveis"] == 0
    assert resultado["totalComServico"] == 0
    assert resultado["vinShareEstimado"] == 0.0


def test_filtro_com_caracteres_especiais_nao_quebra() -> None:
    resultado = compute_vin_share(_historico(), modelo="RANGER'; DROP TABLE veiculos; --")

    assert resultado["totalVeiculosElegiveis"] == 0
    assert resultado["totalComServico"] == 0


@pytest.mark.parametrize("kwargs", [
    {},
    {"modelo": "RANGER"},
    {"faixa_idade": "0-1"},
    {"tipo_servico": "Recall"},
    {"concessionaria": "100"},
    {"modelo": "RANGER", "tipo_servico": "Recall", "faixa_idade": "0-1"},
    {"modelo": "MODELO_INEXISTENTE"},
])
def test_com_servico_nunca_excede_elegiveis(kwargs: dict) -> None:
    resultado = compute_vin_share(_historico(), **kwargs)

    assert resultado["totalComServico"] <= resultado["totalVeiculosElegiveis"]
    assert 0.0 <= resultado["vinShareEstimado"] <= 100.0
