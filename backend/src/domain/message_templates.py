"""Mensagem de contato com o cliente, personalizada por faixa de risco de evasão."""
from __future__ import annotations

from src.domain.action_rules import Acao

# Tom deliberadamente crescente em urgência mas nunca alarmista — mesmo em "contato_ativo"
# a mensagem é um convite, não um aviso de problema. Cita sempre o modelo do veículo e há
# quantos dias ele está sem revisão (a "visão 360°" pedida no plano), nunca o score ou o
# rótulo de risco em si — isso é informação interna, não algo para mostrar ao cliente.
TEMPLATES: dict[Acao, str] = {
    "lembrete": (
        "Olá! Notamos que já faz {dias} dias desde a última revisão do seu {modelo} "
        "na {concessionaria}. Que tal agendar uma manutenção preventiva quando for "
        "conveniente para você?"
    ),
    "oferta": (
        "Olá! Seu {modelo} está há {dias} dias sem passar por uma revisão na "
        "{concessionaria}. Preparamos uma condição especial de manutenção para você — "
        "entre em contato para saber mais."
    ),
    "contato_ativo": (
        "Olá! Já faz {dias} dias desde a última manutenção do seu {modelo}, bem acima "
        "do intervalo recomendado. Um consultor da {concessionaria} vai entrar em "
        "contato para ajudar a agendar sua revisão o quanto antes."
    ),
}

CONCESSIONARIA_PADRAO = "sua concessionária Ford"


def montar_mensagem(
    acao: Acao,
    modelo: str,
    dias_sem_servico: float,
    concessionaria: str = CONCESSIONARIA_PADRAO,
) -> str:
    """Preenche o template de `acao` (ver `action_rules.recomendar_acao`) com os dados
    reais do veículo.

    `dias_sem_servico` é arredondado para inteiro — "180 dias", não "180.4 dias".
    """
    return TEMPLATES[acao].format(
        modelo=modelo,
        dias=round(dias_sem_servico),
        concessionaria=concessionaria,
    )
