"""Aplica o modelo treinado às features processadas e grava a lista de leads em backend/data/processed/."""
from pathlib import Path

import pandas as pd

from src.application.generate_leads import add_risk_explanation, rank_by_dealer
from src.application.train_risk_model import FEATURE_COLUMNS
from src.infrastructure.model_repository import load_model
from src.interfaces.pipeline.train_model import RAW_PATH, build_dataset

OUTPUT_PATH = "data/processed/leads.csv"

# Schema combinado com o Paulo (front-end) para a tabela de leads do dashboard — mesmo
# contrato já declarado em frontend/src/domain/types.ts::Lead (nome do campo e ordem).
# Chave = coluna de origem na tabela interna; valor = nome de coluna no CSV exportado.
# Não alterar nome/ordem aqui sem realinhar com ele primeiro.
LEADS_SCHEMA: dict[str, str] = {
    "VIN_Hash": "vin",
    "DealerCode": "dealerCode",
    "score_risco": "score",
    "motivo_risco": "motivo",
    "ModelName": "modelo",
}


def build_leads_table(reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Monta a tabela de leads: score do modelo treinado, motivo do risco e concessionária.

    Reaproveita `build_dataset` (mesmas features do treino), o modelo já treinado e
    salvo (`model_repository.load_model`) e `add_risk_explanation`/`rank_by_dealer`
    (issues anteriores) — nenhuma lógica de negócio nova aqui, só orquestração.
    """
    tabela = build_dataset(reference_date=reference_date)
    modelo = load_model()

    leads = tabela.dropna(subset=list(FEATURE_COLUMNS)).copy()
    leads["score_risco"] = modelo.predict_proba(leads[list(FEATURE_COLUMNS)])[:, 1]
    leads = add_risk_explanation(leads)

    df_raw = pd.read_csv(RAW_PATH, compression="zip", low_memory=False)
    dealer_por_vin = (
        df_raw.dropna(subset=["ServiceDate"])
        .sort_values("ServiceDate")
        .groupby("VIN_Hash")["DealerCode"]
        .last()
        .reset_index()
    )
    leads = leads.merge(dealer_por_vin, on="VIN_Hash", how="left")

    return rank_by_dealer(leads, dealer_col="DealerCode", score_col="score_risco")


def export_leads_csv(leads: pd.DataFrame, path: str | Path = OUTPUT_PATH) -> Path:
    """Exporta `leads` para CSV usando só as colunas do `LEADS_SCHEMA`, na ordem exata,
    já renomeadas para o contrato combinado com o Paulo.

    Levanta `KeyError` (com a lista do que falta) se `leads` não tiver alguma das
    colunas de origem esperadas — melhor falhar aqui do que exportar um CSV incompleto
    sem ninguém perceber.
    """
    colunas_origem = list(LEADS_SCHEMA.keys())
    faltando = [coluna for coluna in colunas_origem if coluna not in leads.columns]
    if faltando:
        raise KeyError(f"Colunas do schema de leads ausentes na tabela: {faltando}")

    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    leads[colunas_origem].rename(columns=LEADS_SCHEMA).to_csv(destino, index=False)

    return destino


def main() -> None:
    leads = build_leads_table()
    destino = export_leads_csv(leads)

    print(f"leads.csv gerado: {destino} ({len(leads):,} linhas)")
    print(f"Colunas (ordem combinada com o Paulo): {list(LEADS_SCHEMA.values())}")


if __name__ == "__main__":
    main()
