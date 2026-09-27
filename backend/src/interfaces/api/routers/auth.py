"""Router do endpoint GET/POST /api/auth — login.

Schema de resposta de `POST /api/auth/login`:

    {
      "token": "eyJhbGciOiJIUzI1NiIs...",
      "perfil": "gestor",
      "dealerCode": null,
      "expiraEm": "2026-09-27T20:15:00+00:00"
    }

`perfil` é um de `"gestor" | "concessionaria"`. `dealerCode` é `null` para
`gestor` (acesso à rede toda) e o código do dealer para `concessionaria`
(mesmo valor que fica embutido no token e é usado para escopar as demais
requisições — ver `interfaces.api.dependencies.escopar_concessionaria`).

Único endpoint público da API (além de `/health` e da documentação em
`/docs`) — todo o resto exige `Authorization: Bearer <token>`.

401 em usuário inexistente ou senha incorreta — a mensagem não diferencia os
dois casos ("credenciais inválidas" genérico), pra não revelar se um
usuário existe ou não.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.domain.security import Perfil, criar_token, verificar_senha
from src.infrastructure.user_repository import buscar_usuario

router = APIRouter()


class CredenciaisLogin(BaseModel):
    usuario: str
    senha: str


class TokenAcesso(BaseModel):
    token: str
    perfil: Perfil
    dealerCode: str | None
    expiraEm: str


@router.post("/auth/login", response_model=TokenAcesso, status_code=200)
def login(credenciais: CredenciaisLogin) -> TokenAcesso:
    registro = buscar_usuario(credenciais.usuario)

    if registro is None or not verificar_senha(credenciais.senha, registro.senha_hash):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")

    token, expira_em = criar_token(registro.usuario, registro.perfil, registro.dealer_code)

    return TokenAcesso(
        token=token,
        perfil=registro.perfil,
        dealerCode=registro.dealer_code,
        expiraEm=expira_em.isoformat(),
    )
