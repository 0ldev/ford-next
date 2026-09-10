"""Prioridade final de contato: cruza risco de evasão com valor do cliente.

Evita desperdiçar esforço de contato em veículos de baixo retorno (plano, Pilar 3) —
um veículo de risco alto mas que nunca gerou receita de pós-venda não deveria furar a
fila na frente de um cliente fiel de risco médio.
"""
from __future__ import annotations

import pandas as pd

# "Valor do cliente" = nº de serviços já realizados (n_servicos, já calculado na issue
# #24) — é o proxy mais direto de receita histórica de pós-venda disponível na tabela de
# features, sem precisar de dado financeiro que o dataset não tem.
#
# VALOR_CLIENTE_TETO = 8 vem da distribuição real de n_servicos em
# backend/data/processed/vehicle_features.parquet (175.554 VINs): mediana 2, p90 6,
# p95 8, máx 35. Usar o máximo bruto (35) faria a normalização linear esmagar 95% da
# base perto de 0 por causa de poucos veículos extremos (frota/uso atípico). Cortar no
# p95 (8) reconhece que a diferença de valor entre "8 serviços" e "35 serviços" é
# marginal para fins de priorização de contato — os dois são claramente clientes de
# alto valor — enquanto ainda distingue bem a faixa onde a maioria da base está.
VALOR_CLIENTE_TETO = 8


def compute_valor_cliente(n_servicos: pd.Series, teto: int = VALOR_CLIENTE_TETO) -> pd.Series:
    """Valor do cliente normalizado em [0, 1] a partir do nº de serviços já realizados.

    `n_servicos >= teto` satura em 1.0 (ver `VALOR_CLIENTE_TETO`). `n_servicos` nulo
    produz valor nulo (não 0 — "sem dado" não é o mesmo que "sem valor").
    """
    return (n_servicos.clip(upper=teto) / teto).rename("valor_cliente")


def compute_prioridade(
    score_risco: pd.Series,
    valor_cliente: pd.Series,
    peso_risco: float = 0.7,
    peso_valor: float = 0.3,
) -> pd.Series:
    """Prioridade final de contato: média ponderada de risco e valor do cliente, em [0, 1].

    Risco pesa mais (`peso_risco=0.7` por padrão) porque é o sinal principal do
    desafio — a camada de valor existe para DESEMPATAR e redistribuir esforço dentro
    de uma lista já ordenada por risco, não para substituir o risco como critério
    principal. Um VIN de risco alto (1.0) e valor baixo (0.0) ainda fica à frente de um
    VIN de risco médio (0.5) e valor alto (1.0) com os pesos padrão (0.7 vs. 0.65) —
    intencional: risco de evasão iminente não deveria esperar o cliente "provar valor".

    `peso_risco + peso_valor` não precisa somar 1 (a função não normaliza) — os
    valores padrão somam 1 só por serem os mais fáceis de interpretar como percentual.

    Nulo quando `score_risco` ou `valor_cliente` for nulo (não dá para priorizar sem
    os dois sinais).
    """
    return (peso_risco * score_risco + peso_valor * valor_cliente).rename("prioridade")
