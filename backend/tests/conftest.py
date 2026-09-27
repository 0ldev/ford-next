"""Fixtures compartilhadas de autenticação para os testes de API.

Todo endpoint agora exige `Authorization: Bearer <token>` — estas fixtures
dão um token válido de cada perfil sem precisar bater em `/api/auth/login`
(mais rápido, e não acopla os testes de outros routers ao de login).
"""
import pytest

from src.domain.security import criar_token

DEALER_CONCESSIONARIA_TESTE = "6693"


@pytest.fixture
def token_gestor() -> str:
    token, _ = criar_token("gestor", "gestor", dealer_code=None)
    return token


@pytest.fixture
def token_concessionaria() -> str:
    token, _ = criar_token("concessionaria6693", "concessionaria", dealer_code=DEALER_CONCESSIONARIA_TESTE)
    return token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
