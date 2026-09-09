import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.infrastructure.model_repository import load_model, save_model, verify_round_trip


class _ModeloComPredictProbaInconsistente:
    """Simula um artefato corrompido/divergente: retorna previsões diferentes a cada chamada.

    Definida no nível do módulo (não dentro do teste) porque joblib/pickle não
    conseguem serializar uma classe aninhada dentro de uma função.
    """

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.random.default_rng().uniform(size=(len(X), 2))


@pytest.fixture
def modelo_treinado() -> tuple[LogisticRegression, pd.DataFrame]:
    rng = np.random.default_rng(0)
    X = pd.DataFrame({
        "idade_dias": rng.uniform(30, 3000, 100),
        "gap_com_fallback": rng.uniform(0, 5, 100),
        "n_servicos": rng.integers(1, 20, 100),
    })
    y = (X["gap_com_fallback"] > 1.5).astype(int)

    modelo = LogisticRegression()
    modelo.fit(X, y)

    return modelo, X


def test_save_model_cria_arquivo_pkl(tmp_path, modelo_treinado) -> None:
    modelo, _ = modelo_treinado
    destino = save_model(modelo, tmp_path / "modelo.pkl")

    assert destino.exists()
    assert destino.suffix == ".pkl"


def test_save_model_cria_diretorio_de_destino_se_nao_existir(tmp_path, modelo_treinado) -> None:
    modelo, _ = modelo_treinado
    destino = save_model(modelo, tmp_path / "subpasta_nova" / "modelo.pkl")

    assert destino.exists()


def test_load_model_carrega_de_volta_sem_erro(tmp_path, modelo_treinado) -> None:
    modelo, X = modelo_treinado
    destino = save_model(modelo, tmp_path / "modelo.pkl")

    modelo_carregado = load_model(destino)

    assert hasattr(modelo_carregado, "predict_proba")
    modelo_carregado.predict_proba(X)  # nao deve levantar erro


def test_previsoes_identicas_antes_e_depois_de_salvar(tmp_path, modelo_treinado) -> None:
    modelo, X = modelo_treinado
    proba_antes = modelo.predict_proba(X)

    destino = save_model(modelo, tmp_path / "modelo.pkl")
    modelo_carregado = load_model(destino)
    proba_depois = modelo_carregado.predict_proba(X)

    assert np.array_equal(proba_antes, proba_depois)


def test_verify_round_trip_confirma_previsoes_identicas(tmp_path, modelo_treinado) -> None:
    modelo, X = modelo_treinado
    destino = verify_round_trip(modelo, X, path=tmp_path / "modelo.pkl")

    assert destino.exists()


def test_verify_round_trip_detecta_divergencia(tmp_path, modelo_treinado) -> None:
    _, X = modelo_treinado

    with pytest.raises(AssertionError):
        verify_round_trip(_ModeloComPredictProbaInconsistente(), X, path=tmp_path / "modelo.pkl")
