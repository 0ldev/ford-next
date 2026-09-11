"""Distribuição do score de risco dos leads — schema de GET /api/leads/distribuicao-score."""
from __future__ import annotations

import pandas as pd

N_FAIXAS_PADRAO = 10


def compute_score_distribution(df: pd.DataFrame, n_faixas: int = N_FAIXAS_PADRAO) -> list[dict]:
    """Quantidade de leads por faixa de score, em `n_faixas` faixas de largura igual (0-100%).

    Cada faixa é `(faixaInicio, faixaFim]`, exceto a primeira, que inclui o 0 (nenhum
    lead com `score` negativo fica de fora por isso). Retorna uma linha por faixa, na
    ordem 0 -> 100%, mesmo quando `quantidade` é 0 (sem isso o gráfico teria barras
    faltando em vez de barras zeradas).

    Existe para expor a distribuição REAL do score — o endpoint de leads prioritários
    só devolve o top 50, então não dá pra ver por ele que a distribuição é fortemente
    bimodal (ver `domain.action_rules`: ~27% em risco baixo, ~2% no meio, ~71% em risco
    alto). `df` é o `leads.csv` inteiro (~175 mil linhas), não o recorte do endpoint
    `/leads`.
    """
    limites = [i / n_faixas for i in range(n_faixas + 1)]
    faixas = pd.cut(df["score"], bins=limites, include_lowest=True, right=True)

    contagem = faixas.value_counts().sort_index()

    return [
        {
            # `pd.cut(include_lowest=True)` desloca a borda esquerda do primeiro
            # intervalo para um pouco abaixo de 0 (ex.: -0.001), só pra incluir o 0.0
            # sem quebrar a regra de intervalo semiaberto — não é o "-0,1%" real.
            "faixaInicio": round(max(intervalo.left, 0.0) * 100, 1),
            "faixaFim": round(intervalo.right * 100, 1),
            "quantidade": int(quantidade),
        }
        for intervalo, quantidade in contagem.items()
    ]
