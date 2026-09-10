import pandas as pd
import pytest

from src.application.gap_zscore_prototype import (
    compute_em_risco_hibrido,
    compute_gap_zscore,
    compute_vehicle_own_gap_stats,
)


def test_compute_vehicle_own_gap_stats_exige_3_servicos() -> None:
    df = pd.DataFrame({
        "VIN_Hash": ["v1", "v1", "v1", "v2", "v2"],
        "ServiceDate": pd.to_datetime([
            "2024-01-01", "2024-04-01", "2024-07-01",  # v1: 3 servicos, 2 intervalos
            "2024-01-01", "2024-06-01",  # v2: 2 servicos, 1 intervalo (std nulo)
        ]),
    })

    resultado = compute_vehicle_own_gap_stats(df).set_index("VIN_Hash")

    assert resultado.loc["v1", "media_gap_proprio"] == 91.0  # (91+91)/2
    assert pd.notna(resultado.loc["v1", "desvio_padrao_gaps"])
    assert pd.isna(resultado.loc["v2", "desvio_padrao_gaps"])


def test_gap_zscore_positivo_quando_atrasado_em_relacao_ao_proprio_padrao() -> None:
    dias = pd.Series([300.0])
    media = pd.Series([100.0])
    desvio = pd.Series([50.0])

    resultado = compute_gap_zscore(dias, media, desvio)

    assert resultado.iloc[0] == 4.0  # (300-100)/50


def test_gap_zscore_nulo_quando_desvio_e_zero() -> None:
    resultado = compute_gap_zscore(pd.Series([300.0]), pd.Series([100.0]), pd.Series([0.0]))
    assert resultado.isna().all()


def test_gap_zscore_nulo_quando_desvio_e_nulo() -> None:
    resultado = compute_gap_zscore(pd.Series([300.0]), pd.Series([100.0]), pd.Series([None]))
    assert resultado.isna().all()


def test_em_risco_hibrido_usa_zscore_quando_disponivel() -> None:
    gap_zscore = pd.Series([2.0, 0.5])  # v1 acima do threshold, v2 abaixo
    gap_com_fallback = pd.Series([0.1, 0.1])  # baixo nos dois, nao deveria ser usado aqui

    resultado = compute_em_risco_hibrido(gap_zscore, gap_com_fallback, threshold_zscore=1.5)

    assert resultado.iloc[0]
    assert not resultado.iloc[1]


def test_em_risco_hibrido_cai_para_fallback_quando_sem_zscore() -> None:
    gap_zscore = pd.Series([None])
    gap_com_fallback = pd.Series([3.0])  # acima do threshold_gap_fallback padrao (2.0)

    resultado = compute_em_risco_hibrido(gap_zscore, gap_com_fallback)

    assert resultado.iloc[0]


def test_veiculo_erratico_mas_fiel_nao_e_mais_marcado_como_risco() -> None:
    """Caso motivador do protótipo: veículo com histórico irregular (média 200, desvio
    120) atualmente a 300 dias — bem menos de 1 desvio acima da própria média, então
    NÃO deveria ser marcado como em risco pelo z-score, mesmo que 300 já ultrapasse
    um threshold populacional fixo tipo "2x a mediana do modelo"."""
    gap_zscore = compute_gap_zscore(
        dias_desde_ultimo_servico=pd.Series([300.0]),
        media_gap_proprio=pd.Series([200.0]),
        desvio_padrao_gaps=pd.Series([120.0]),
    )
    resultado = compute_em_risco_hibrido(gap_zscore, gap_com_fallback=pd.Series([0.0]))

    assert gap_zscore.iloc[0] == pytest.approx(0.833, abs=0.01)
    assert not resultado.iloc[0]
