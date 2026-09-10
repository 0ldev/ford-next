"""Leitura (com cache em memória) da lista de leads processada para /api/leads."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

LEADS_PATH = "data/processed/leads.csv"


@lru_cache(maxsize=4)
def _load(path: str) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Lista de leads não encontrada em '{path}'. Gere-a antes de subir a API "
            "(a partir de backend/): `python -m src.interfaces.pipeline.build_features` "
            "seguido de `train_model` e `generate_leads`."
        )

    df = pd.read_csv(path)
    # O CSV grava dealerCode como numero; o contrato combinado com o front-end
    # (frontend/src/domain/types.ts::Lead.dealerCode) e' string.
    df["dealerCode"] = df["dealerCode"].astype(str)

    return df


def load_leads_data(path: str | Path = LEADS_PATH) -> pd.DataFrame:
    """Lê `data/processed/leads.csv`, gerado por `interfaces.pipeline.generate_leads`.

    O resultado fica em cache em memória por `path` (`lru_cache`): a leitura do CSV
    roda só na primeira chamada. Chamadas seguintes reaproveitam o mesmo DataFrame.
    """
    return _load(str(path))
