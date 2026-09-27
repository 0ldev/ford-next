import pytest

from src.domain.authorization import (
    AcessoNegadoError,
    filtrar_anomalias_por_perfil,
    filtrar_concessionarias_visiveis,
    resolver_escopo_concessionaria,
    resolver_escopo_concessionarias,
    verificar_acesso_ao_dealer,
)


# --------------------------------------------------------------------------- #
# resolver_escopo_concessionaria                                               #
# --------------------------------------------------------------------------- #

def test_gestor_sem_filtro_pedido_passa_livre_rede_toda() -> None:
    assert resolver_escopo_concessionaria("gestor", None, None) is None


def test_gestor_com_filtro_pedido_passa_o_filtro_como_veio() -> None:
    assert resolver_escopo_concessionaria("gestor", None, "6693") == "6693"


def test_concessionaria_sem_filtro_pedido_e_auto_escopada_pro_proprio_dealer() -> None:
    assert resolver_escopo_concessionaria("concessionaria", "6693", None) == "6693"


def test_concessionaria_pedindo_o_proprio_dealer_e_permitido() -> None:
    assert resolver_escopo_concessionaria("concessionaria", "6693", "6693") == "6693"


def test_concessionaria_pedindo_outro_dealer_e_negado() -> None:
    with pytest.raises(AcessoNegadoError):
        resolver_escopo_concessionaria("concessionaria", "6693", "9999")


# --------------------------------------------------------------------------- #
# resolver_escopo_concessionarias (lista, GET /trend/concessionarias)          #
# --------------------------------------------------------------------------- #

def test_gestor_lista_sem_filtro_passa_livre() -> None:
    assert resolver_escopo_concessionarias("gestor", None, None) is None


def test_gestor_lista_com_filtro_passa_a_lista_como_veio() -> None:
    assert resolver_escopo_concessionarias("gestor", None, ["6693", "9999"]) == ["6693", "9999"]


def test_concessionaria_lista_vazia_e_auto_escopada() -> None:
    assert resolver_escopo_concessionarias("concessionaria", "6693", None) == ["6693"]
    assert resolver_escopo_concessionarias("concessionaria", "6693", []) == ["6693"]


def test_concessionaria_lista_so_com_o_proprio_dealer_e_permitida() -> None:
    assert resolver_escopo_concessionarias("concessionaria", "6693", ["6693"]) == ["6693"]


def test_concessionaria_lista_com_qualquer_outro_dealer_e_negada() -> None:
    # mesmo que o proprio dealer esteja incluso, a presenca de QUALQUER outro
    # recusa a requisicao inteira -- nao filtra silenciosamente a lista.
    with pytest.raises(AcessoNegadoError):
        resolver_escopo_concessionarias("concessionaria", "6693", ["6693", "9999"])


# --------------------------------------------------------------------------- #
# verificar_acesso_ao_dealer (recurso unico, ex.: /leads/{vin}/acao)           #
# --------------------------------------------------------------------------- #

def test_gestor_acessa_recurso_de_qualquer_dealer() -> None:
    verificar_acesso_ao_dealer("gestor", None, "9999")  # nao levanta


def test_concessionaria_acessa_recurso_do_proprio_dealer() -> None:
    verificar_acesso_ao_dealer("concessionaria", "6693", "6693")  # nao levanta


def test_concessionaria_nao_acessa_recurso_de_outro_dealer() -> None:
    with pytest.raises(AcessoNegadoError):
        verificar_acesso_ao_dealer("concessionaria", "6693", "9999")


# --------------------------------------------------------------------------- #
# filtrar_concessionarias_visiveis (GET /catalogo)                             #
# --------------------------------------------------------------------------- #

def test_gestor_ve_todas_as_concessionarias_do_catalogo() -> None:
    todas = ["100", "200", "6693"]
    assert filtrar_concessionarias_visiveis("gestor", None, todas) == todas


def test_concessionaria_so_ve_o_proprio_codigo_no_catalogo() -> None:
    todas = ["100", "200", "6693"]
    assert filtrar_concessionarias_visiveis("concessionaria", "6693", todas) == ["6693"]


def test_concessionaria_nao_aparece_lista_vazia_se_o_proprio_dealer_nao_estiver_no_catalogo() -> None:
    # Nao deveria acontecer na pratica (o proprio login so' existe pra dealers
    # reais), mas a funcao nao pode quebrar nem inventar uma entrada.
    assert filtrar_concessionarias_visiveis("concessionaria", "6693", ["100", "200"]) == []


# --------------------------------------------------------------------------- #
# filtrar_anomalias_por_perfil (GET /anomalies, GET /resumo-executivo)         #
# --------------------------------------------------------------------------- #

def _anomalia(tipo: str, entidade: str) -> dict:
    return {"tipo": tipo, "entidade": entidade, "severidade": 0.5, "resumo": "r", "descricao": "d",
            "valorReferencia": 1.0, "valorAtual": 2.0}


def test_gestor_ve_todas_as_anomalias() -> None:
    anomalias = [_anomalia("queda_dealer", "100"), _anomalia("pico_mainsource", "200"), _anomalia("gap_modelo", "KA")]
    assert filtrar_anomalias_por_perfil("gestor", None, anomalias) == anomalias


def test_concessionaria_so_ve_queda_dealer_e_pico_mainsource_do_proprio_dealer() -> None:
    anomalias = [
        _anomalia("queda_dealer", "6693"),
        _anomalia("queda_dealer", "9999"),
        _anomalia("pico_mainsource", "6693"),
        _anomalia("pico_mainsource", "9999"),
    ]
    resultado = filtrar_anomalias_por_perfil("concessionaria", "6693", anomalias)

    assert len(resultado) == 2
    assert all(item["entidade"] == "6693" for item in resultado)


def test_concessionaria_ve_gap_modelo_de_qualquer_modelo_mesmo_assim() -> None:
    # gap_modelo nao tem dimensao de dealer (entidade e' um ModelName) -- e'
    # sinal de rede, continua visivel independente do dealer do usuario.
    anomalias = [_anomalia("gap_modelo", "KA"), _anomalia("gap_modelo", "RANGER")]
    assert filtrar_anomalias_por_perfil("concessionaria", "6693", anomalias) == anomalias
