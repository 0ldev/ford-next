"""Regras de escopo por perfil de acesso — funções puras, sem HTTP.

Só 2 perfis: `"gestor"` (acesso à rede inteira) e `"concessionaria"` (travado
no próprio `dealerCode`). Reaproveita o conceito de `concessionaria` que já
existe em `vin_share`, `leads` e `trend/concessionarias` — a regra de negócio
é literalmente "um usuário de concessionária só vê o que já era filtrável
pelo próprio dealer", não uma dimensão de permissão nova.
"""
from __future__ import annotations

from src.domain.security import Perfil


class AcessoNegadoError(Exception):
    """Perfil `concessionaria` pedindo dado de um dealer que não é o seu."""


def resolver_escopo_concessionaria(
    perfil: Perfil, dealer_code_usuario: str | None, concessionaria_solicitada: str | None
) -> str | None:
    """O `dealerCode` que deve efetivamente filtrar a consulta.

    - `gestor`: passa livre — devolve `concessionaria_solicitada` como veio
      (inclusive `None`, que significa "rede toda").
    - `concessionaria`: sem filtro pedido, é auto-escopado pro próprio dealer
      (nunca vê a rede toda); pedindo o próprio dealer, ok; pedindo outro
      dealer, `AcessoNegadoError`.
    """
    if perfil == "gestor":
        return concessionaria_solicitada

    if concessionaria_solicitada is None:
        return dealer_code_usuario

    if concessionaria_solicitada != dealer_code_usuario:
        raise AcessoNegadoError(
            f"Perfil concessionaria não pode acessar dados do dealer '{concessionaria_solicitada}'."
        )

    return concessionaria_solicitada


def resolver_escopo_concessionarias(
    perfil: Perfil, dealer_code_usuario: str | None, concessionarias_solicitadas: list[str] | None
) -> list[str] | None:
    """Mesma regra de `resolver_escopo_concessionaria`, para o filtro repetível
    (`?concessionaria=A&concessionaria=B`) de `GET /trend/concessionarias`.

    `gestor` passa livre. `concessionaria` sem lista é auto-escopado pra
    `[dealer_code_usuario]` (nunca vê a rede toda); pedindo alguma
    concessionária que não seja a própria (mesmo entre outras válidas),
    `AcessoNegadoError` — não filtra silenciosamente, recusa a requisição
    inteira, pra não sugerir que uma lista parcial foi "aceita".
    """
    if perfil == "gestor":
        return concessionarias_solicitadas

    if not concessionarias_solicitadas:
        return [dealer_code_usuario] if dealer_code_usuario else None

    if any(codigo != dealer_code_usuario for codigo in concessionarias_solicitadas):
        raise AcessoNegadoError("Perfil concessionaria só pode acessar dados do próprio dealer.")

    return concessionarias_solicitadas


def verificar_acesso_ao_dealer(perfil: Perfil, dealer_code_usuario: str | None, dealer_code_alvo: str) -> None:
    """Para recursos de um dealer específico (ex.: o dealer de UM lead/VIN).

    `gestor` sempre passa. `concessionaria` só passa se `dealer_code_alvo` for
    o próprio — `AcessoNegadoError` caso contrário.
    """
    if perfil == "gestor":
        return

    if dealer_code_alvo != dealer_code_usuario:
        raise AcessoNegadoError(
            f"Perfil concessionaria não pode acessar recursos do dealer '{dealer_code_alvo}'."
        )


def filtrar_concessionarias_visiveis(
    perfil: Perfil, dealer_code_usuario: str | None, todas: list[str]
) -> list[str]:
    """Recorta uma lista de dealers pro que o perfil pode efetivamente ver.

    Diferente de `resolver_escopo_concessionaria` (que valida um pedido e
    recusa com erro): aqui não há "pedido" — é uma lista de catálogo/relatório
    que já ia ser devolvida inteira, e precisa ser filtrada em silêncio antes
    de sair. `gestor` vê tudo; `concessionaria` só o próprio dealer (presente
    ou não em `todas`).
    """
    if perfil == "gestor":
        return todas

    return [codigo for codigo in todas if codigo == dealer_code_usuario]


def filtrar_anomalias_por_perfil(
    perfil: Perfil, dealer_code_usuario: str | None, anomalias: list[dict]
) -> list[dict]:
    """Recorta a lista de anomalias pro que o perfil pode ver.

    `gestor` vê tudo. `concessionaria` só vê `queda_dealer`/`pico_mainsource`
    do próprio dealer (`entidade` é o `DealerCode` nesses dois tipos — ver
    `application.anomaly_detection`) — `gap_modelo` não tem essa dimensão
    (`entidade` é um `ModelName`) e continua visível a todos, é sinal de rede,
    não de uma concessionária específica.
    """
    if perfil == "gestor":
        return anomalias

    return [
        anomalia
        for anomalia in anomalias
        if anomalia["tipo"] == "gap_modelo" or anomalia["entidade"] == dealer_code_usuario
    ]
