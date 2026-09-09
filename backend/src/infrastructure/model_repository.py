"""Persistência do modelo de risco treinado como artefato joblib, em backend/models/."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
DEFAULT_MODEL_FILENAME = "risk_model.pkl"


def save_model(modelo: Any, path: str | Path | None = None) -> Path:
    """Salva `modelo` (qualquer estimador scikit-learn) em `path` via joblib.

    Cria o diretório de destino se não existir. Sem `path`, salva em
    `backend/models/risk_model.pkl`. Retorna o `Path` efetivamente usado.
    """
    destino = Path(path) if path is not None else MODELS_DIR / DEFAULT_MODEL_FILENAME
    destino.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, destino)

    return destino


def load_model(path: str | Path | None = None) -> Any:
    """Carrega de volta um modelo salvo com `save_model`."""
    origem = Path(path) if path is not None else MODELS_DIR / DEFAULT_MODEL_FILENAME
    return joblib.load(origem)


def verify_round_trip(modelo: Any, X: pd.DataFrame, path: str | Path | None = None) -> Path:
    """Salva `modelo`, carrega de volta e confirma que `predict_proba(X)` bate exatamente.

    Levanta `AssertionError` se as previsões do modelo carregado divergirem das do
    modelo original em `X`. Retorna o `Path` onde o artefato ficou salvo.
    """
    proba_antes = modelo.predict_proba(X)
    destino = save_model(modelo, path)
    modelo_carregado = load_model(destino)
    proba_depois = modelo_carregado.predict_proba(X)

    if not np.array_equal(proba_antes, proba_depois):
        raise AssertionError(
            "As previsoes do modelo carregado de volta nao batem com as do modelo original"
        )

    return destino
