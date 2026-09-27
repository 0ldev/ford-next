import pytest

from src.domain.authorization import (
    AcessoNegadoError,
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
