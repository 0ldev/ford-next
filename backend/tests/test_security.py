import time

import jwt
import pytest

from src.domain.security import (
    JWT_ALGORITHM,
    JWT_SECRET,
    TokenInvalidoError,
    criar_token,
    decodificar_token,
    hash_senha,
    verificar_senha,
)


def test_hash_senha_gera_valores_diferentes_para_a_mesma_senha() -> None:
    # Salt aleatorio: dois hashes da mesma senha nao devem ser iguais (senao um
    # dump do "banco" revelaria senhas repetidas so' de bater os hashes).
    assert hash_senha("minhasenha123") != hash_senha("minhasenha123")


def test_verificar_senha_aceita_a_senha_correta() -> None:
    hash_armazenado = hash_senha("minhasenha123")
    assert verificar_senha("minhasenha123", hash_armazenado) is True


def test_verificar_senha_rejeita_senha_errada() -> None:
    hash_armazenado = hash_senha("minhasenha123")
    assert verificar_senha("outrasenha", hash_armazenado) is False


def test_verificar_senha_com_hash_malformado_nao_quebra() -> None:
    assert verificar_senha("qualquer", "hash-sem-separador") is False
    assert verificar_senha("qualquer", "") is False


def test_criar_token_e_decodificar_token_fazem_roundtrip() -> None:
    token, expira_em = criar_token("gestor", "gestor", dealer_code=None)
    payload = decodificar_token(token)

    assert payload.usuario == "gestor"
    assert payload.perfil == "gestor"
    assert payload.dealer_code is None
    assert expira_em.timestamp() > time.time()


def test_criar_token_preserva_dealer_code_do_perfil_concessionaria() -> None:
    token, _ = criar_token("concessionaria6693", "concessionaria", dealer_code="6693")
    payload = decodificar_token(token)

    assert payload.perfil == "concessionaria"
    assert payload.dealer_code == "6693"


def test_decodificar_token_expirado_levanta_erro() -> None:
    token, _ = criar_token("gestor", "gestor", expira_em_minutos=-1)

    with pytest.raises(TokenInvalidoError):
        decodificar_token(token)


def test_decodificar_token_com_assinatura_adulterada_levanta_erro() -> None:
    token, _ = criar_token("gestor", "gestor")
    token_adulterado = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(TokenInvalidoError):
        decodificar_token(token_adulterado)


def test_decodificar_token_assinado_com_outro_segredo_levanta_erro() -> None:
    token_forjado = jwt.encode({"sub": "gestor", "perfil": "gestor", "dealerCode": None}, "outro-segredo", algorithm=JWT_ALGORITHM)

    with pytest.raises(TokenInvalidoError):
        decodificar_token(token_forjado)


def test_decodificar_token_sem_claim_obrigatoria_levanta_erro() -> None:
    token_incompleto = jwt.encode({"sub": "gestor"}, JWT_SECRET, algorithm=JWT_ALGORITHM)

    with pytest.raises(TokenInvalidoError):
        decodificar_token(token_incompleto)


def test_decodificar_token_garbage_levanta_erro() -> None:
    with pytest.raises(TokenInvalidoError):
        decodificar_token("isso-nao-e-um-jwt")
