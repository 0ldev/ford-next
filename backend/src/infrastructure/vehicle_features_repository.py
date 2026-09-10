"""Leitura (com cache em memória) da tabela de features processada para /api/leads/{vin}/acao."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.interfaces.pipeline.build_features import FEATURES_PATH


@lru_cache(maxsize=4)
def _load(path: str) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Tabela de features não encontrada em '{path}'. Gere-a antes de subir a API "
            "(a partir de backend/): `python -m src.interfaces.pipeline.build_features`."
        )

    return pd.read_parquet(path)


def load_vehicle_features(path: str | Path = FEATURES_PATH) -> pd.DataFrame:
    """Lê `data/processed/vehicle_features.parquet`, gerado por `interfaces.pipeline.build_features`.

    O resultado fica em cache em memória por `path` (`lru_cache`) — mesmo motivo de
    `vin_share_repository.load_vin_share_data`/`leads_repository.load_leads_data`: sem
    isso, `GET /api/leads/{vin}/acao` relia o parquet do disco a cada requisição em vez
    de reaproveitar o mesmo DataFrame já carregado.
    """
    return _load(str(path))
