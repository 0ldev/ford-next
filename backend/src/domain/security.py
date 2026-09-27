"""Hash de senha e geração/validação de JWT — funções puras, sem I/O.

Separado de `infrastructure.user_repository` (que guarda os usuários) e de
`interfaces.api.dependencies` (que traduz falha de token em `HTTPException`) —
mesma separação de camadas do resto do projeto: aqui só a regra, sem acesso a
dado nem a HTTP.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

Perfil = Literal["gestor", "concessionaria"]

# Em produção isso TEM que vir de variável de ambiente — o fallback existe só
# pra dev local não travar sem configuração nenhuma. `python -m uvicorn` sem
# `JWT_SECRET` no ambiente usa esse valor, o que é aceitável pro desafio mas
# nunca seria para um sistema real.
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-inseguro-trocar-em-producao")
JWT_ALGORITHM = "HS256"
JWT_EXPIRA_MINUTOS = 60

# Iterações do PBKDF2 — valor recomendado atual (OWASP, 2023) pra SHA-256.
PBKDF2_ITERACOES = 600_000


class TokenInvalidoError(Exception):
    """Token ausente, malformado, com assinatura inválida ou expirado."""


@dataclass(frozen=True)
class TokenPayload:
    usuario: str
    perfil: Perfil
    dealer_code: str | None


def hash_senha(senha: str) -> str:
    """Hash de senha via PBKDF2-HMAC-SHA256, salt aleatório embutido no resultado.

    Formato: `"<salt_hex>:<hash_hex>"` — sem isso, verificar a senha depois
    precisaria guardar o salt em algum outro lugar.
    """
    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERACOES)
    return f"{salt}:{hash_bytes.hex()}"


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Confere `senha` contra um hash gerado por `hash_senha`.

    `hmac.compare_digest` (via `secrets.compare_digest`) evita timing attack —
    comparar hex string com `==` vaza quantos bytes iniciais bateram.
    """
    salt, _, hash_esperado = hash_armazenado.partition(":")
    if not salt or not hash_esperado:
        return False

    hash_bytes = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERACOES)
    return secrets.compare_digest(hash_bytes.hex(), hash_esperado)


def criar_token(
    usuario: str,
    perfil: Perfil,
    dealer_code: str | None = None,
    expira_em_minutos: int = JWT_EXPIRA_MINUTOS,
) -> tuple[str, datetime]:
    """Gera um JWT assinado (HS256) e devolve `(token, expira_em)`.

    Claims: `sub` (usuário), `perfil`, `dealerCode` (`None` pra perfil `gestor`),
    `iat`/`exp` (emissão/expiração, em epoch — padrão JWT, não ISO string).
    """
    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(minutes=expira_em_minutos)

    payload = {
        "sub": usuario,
        "perfil": perfil,
        "dealerCode": dealer_code,
        "iat": agora,
        "exp": expira_em,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token, expira_em


def decodificar_token(token: str) -> TokenPayload:
    """Valida assinatura e expiração e devolve os claims. `TokenInvalidoError` em qualquer falha."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as erro:
        raise TokenInvalidoError(str(erro)) from erro

    try:
        return TokenPayload(
            usuario=payload["sub"],
            perfil=payload["perfil"],
            dealer_code=payload.get("dealerCode"),
        )
    except KeyError as erro:
        raise TokenInvalidoError(f"Claim obrigatória ausente no token: {erro}") from erro
