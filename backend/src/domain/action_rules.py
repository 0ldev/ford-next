"""Ação recomendada a partir do score de risco de evasão, faixas definidas pela Visão."""
from __future__ import annotations

from typing import Literal

Acao = Literal["lembrete", "oferta", "contato_ativo"]

# Faixas definidas a partir da distribuição real do score em backend/data/processed/leads.csv
# (175.554 leads: modelo LogisticRegression para RANGER/KA + heurística de threshold para os
# demais modelos — ver issues #5, #33, #44). A distribuição não é uma reta contínua, é
# fortemente bimodal:
#   score <= 0.2      -> 26,5% da frota
#   0.2 < score < 0.8 ->  1,9% da frota (única faixa realmente "no meio")
#   score >= 0.8      -> 71,5% da frota
# Isso reflete o AUC=1.0 do baseline (issue #33): o modelo separa quase perfeitamente as
# classes, então há pouca massa de verdade ambígua. 0.2/0.8 foram escolhidos por serem
# valores redondos que capturam a mesma proporção (~27%/~2%/~71%) de qualquer corte testado
# entre 0.2-0.3 e 0.7-0.8 — não é um ajuste fino arbitrário, é onde os dados já se separam
# sozinhos. (Nota para o pitch: ~71% em "contato ativo" é um número real a ser discutido
# com honestidade, não suavizado — é consequência direta de como o rótulo proxy foi
# construído, ver issue #51.)
LIMITE_BAIXO = 0.2
LIMITE_ALTO = 0.8


def recomendar_acao(
    score: float,
    limite_baixo: float = LIMITE_BAIXO,
    limite_alto: float = LIMITE_ALTO,
) -> Acao:
    """Ação recomendada para a concessionária a partir do score de risco (0-1).

    - `score <= limite_baixo`: risco baixo -> `"lembrete"` simples.
    - `limite_baixo < score < limite_alto`: risco médio -> `"oferta"` com desconto.
    - `score >= limite_alto`: risco alto -> `"contato_ativo"` da concessionária.

    Os limites são inclusivos nas duas pontas: todo `score` cai em exatamente uma das
    três categorias, não há faixa "sem ação" entre elas.
    """
    if score <= limite_baixo:
        return "lembrete"
    if score >= limite_alto:
        return "contato_ativo"
    return "oferta"
