"""Leitura (com cache em memória) do histórico de serviços processado para /api/vin-share."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.interfaces.pipeline.build_service_history import SERVICE_HISTORY_PATH


@lru_cache(maxsize=4)
def _load(path: str) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Histórico de serviços não encontrado em '{path}'. Gere-o antes de subir a API: "
            "`python -m src.interfaces.pipeline.build_service_history` (a partir de backend/)."
        )

    df = pd.read_parquet(path)

    # pandas 3 grava colunas de texto no dtype `str` por padrao, cujo `.isin()` (usado
    # em compute_vin_share para restringir o historico aos VINs elegiveis) e' ~10x mais
    # lento que o `object` classico nas ~600 mil linhas deste arquivo (0.94s vs 0.09s,
    # medido) — o suficiente para estourar o limite de 1s do endpoint. Convertida uma
    # unica vez aqui (cacheada), nao por requisicao.
    colunas_texto = df.select_dtypes(include="str").columns
    df = df.astype({coluna: object for coluna in colunas_texto})

    return df


def load_vin_share_data(path: str | Path = SERVICE_HISTORY_PATH) -> pd.DataFrame:
    """Lê o histórico de serviços gerado por `build_service_history.export_service_history`.

    O resultado fica em cache em memória por `path` (`lru_cache`): a leitura do parquet
    (~600 mil linhas), incluindo a conversão de dtype descrita acima, roda só na
    primeira chamada. Chamadas seguintes — inclusive as disparadas por uma requisição
    HTTP — reaproveitam o mesmo DataFrame, essencial para o endpoint responder em menos
    de 1s.
    """
    return _load(str(path))
