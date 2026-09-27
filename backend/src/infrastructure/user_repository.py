"""Cadastro de usuários — lista fixa (seed), sem banco.

O desafio não pede gestão de usuário (cadastro/edição), só autenticação com
perfis diferentes — uma lista fixa em memória é suficiente e evita introduzir
um banco só para isso. Senhas já vêm hasheadas (`domain.security.hash_senha`),
nunca em texto puro, nem aqui.

Credenciais de demonstração (documentadas também no README):
    gestor            / gestor123   -> perfil "gestor", acesso à rede toda
    concessionaria6693 / dealer123  -> perfil "concessionaria", dealer "6693"
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domain.security import Perfil


@dataclass(frozen=True)
class UsuarioRegistro:
    usuario: str
    senha_hash: str
    perfil: Perfil
    dealer_code: str | None


# Hashes gerados por `domain.security.hash_senha` — ver docstring do módulo
# para a senha em texto puro de cada um (só existe aqui, nunca em produção real).
_USUARIOS_SEED: tuple[UsuarioRegistro, ...] = (
    UsuarioRegistro(
        usuario="gestor",
        senha_hash="1d667be01ecf64848b821fe291e16c9a:4d85c7499be6b0c2604b1313dca24857ea3f1fa696836520731070558f2a38f6",
        perfil="gestor",
        dealer_code=None,
    ),
    UsuarioRegistro(
        usuario="concessionaria6693",
        senha_hash="8879d68897681ed05eca15ae0656fb70:a21bf1de1a6a9ea88a404d05cfa62a96d268a92bb89503a8c833cbd59ecdfffb",
        perfil="concessionaria",
        dealer_code="6693",
    ),
)

_USUARIOS_POR_LOGIN: dict[str, UsuarioRegistro] = {registro.usuario: registro for registro in _USUARIOS_SEED}


def buscar_usuario(usuario: str) -> UsuarioRegistro | None:
    """Busca por nome de usuário (case-sensitive). `None` se não existir."""
    return _USUARIOS_POR_LOGIN.get(usuario)
