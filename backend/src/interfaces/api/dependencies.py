"""Dependências FastAPI compartilhadas entre routers: quem está autenticado e o que pode ver.

Único lugar onde uma falha de `domain.security`/`domain.authorization` vira
`HTTPException` — os módulos de domínio continuam puros (levantam suas
próprias exceções, sem saber o que é HTTP), o mesmo padrão que `trend.py` já
usa pra traduzir `ValueError` da application layer em 422.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain.authorization import (
    AcessoNegadoError,
    resolver_escopo_concessionaria,
    resolver_escopo_concessionarias,
    verificar_acesso_ao_dealer,
)
from src.domain.security import Perfil, TokenInvalidoError, decodificar_token

# `HTTPBearer` como security scheme dá o botão "Authorize" no Swagger de graça
# (FastAPI detecta a dependência e registra o esquema no OpenAPI automaticamente).
_security = HTTPBearer(description="Token JWT obtido em POST /api/auth/login")


@dataclass(frozen=True)
class UsuarioAutenticado:
    usuario: str
    perfil: Perfil
    dealer_code: str | None


def obter_usuario_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(_security),
) -> UsuarioAutenticado:
    """Valida o Bearer token do header `Authorization` e devolve o usuário autenticado.

    401 se o token estiver ausente (o próprio `HTTPBearer` já cobre isso),
    malformado, com assinatura inválida ou expirado.
    """
    try:
        payload = decodificar_token(credenciais.credentials)
    except TokenInvalidoError as erro:
        raise HTTPException(status_code=401, detail=f"Token inválido: {erro}") from erro

    return UsuarioAutenticado(usuario=payload.usuario, perfil=payload.perfil, dealer_code=payload.dealer_code)


def escopar_concessionaria(usuario: UsuarioAutenticado, concessionaria: str | None) -> str | None:
    """`HTTPException(403)` se `usuario` (perfil concessionaria) pedir outro dealer."""
    try:
        return resolver_escopo_concessionaria(usuario.perfil, usuario.dealer_code, concessionaria)
    except AcessoNegadoError as erro:
        raise HTTPException(status_code=403, detail=str(erro)) from erro


def escopar_concessionarias(usuario: UsuarioAutenticado, concessionarias: list[str] | None) -> list[str] | None:
    """`HTTPException(403)` se `usuario` (perfil concessionaria) pedir alguma concessionária que não a própria."""
    try:
        return resolver_escopo_concessionarias(usuario.perfil, usuario.dealer_code, concessionarias)
    except AcessoNegadoError as erro:
        raise HTTPException(status_code=403, detail=str(erro)) from erro


def verificar_dealer_do_recurso(usuario: UsuarioAutenticado, dealer_code_alvo: str) -> None:
    """`HTTPException(403)` se `usuario` (perfil concessionaria) pedir um recurso de outro dealer."""
    try:
        verificar_acesso_ao_dealer(usuario.perfil, usuario.dealer_code, dealer_code_alvo)
    except AcessoNegadoError as erro:
        raise HTTPException(status_code=403, detail=str(erro)) from erro
