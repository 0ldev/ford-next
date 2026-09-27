"""Persistência (append-only, CSV) do histórico de contatos registrados por lead.

Dado gerado em runtime pela própria API (alguém clicou "contato feito"), não
pelo pipeline — por isso mora em `data/runtime/`, separado de `data/processed/`
(saída determinística do pipeline, recriável a qualquer momento). `data/runtime/`
é local e não versionado (ver `.gitignore`).
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.domain.action_rules import Acao

CONTATOS_PATH = "data/runtime/contatos.csv"
_COLUNAS = ("vin", "usuario", "acao", "data")


@dataclass(frozen=True)
class ContatoRegistro:
    vin: str
    usuario: str
    acao: Acao
    data: str  # ISO 8601, UTC — string no dataclass pra serializar direto no CSV/JSON


def _garantir_arquivo(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as arquivo:
        csv.writer(arquivo).writerow(_COLUNAS)


def registrar_contato(vin: str, usuario: str, acao: Acao, path: str | Path | None = None) -> ContatoRegistro:
    """Acrescenta um registro de contato ao histórico do VIN. Nunca sobrescreve — só acrescenta.

    `path=None` (padrão) usa `CONTATOS_PATH` — lido em tempo de chamada, não
    congelado como default do parâmetro, pra testes poderem trocar
    `contatos_repository.CONTATOS_PATH` via monkeypatch e serem respeitados.
    """
    destino = Path(path if path is not None else CONTATOS_PATH)
    _garantir_arquivo(destino)

    registro = ContatoRegistro(vin=vin, usuario=usuario, acao=acao, data=datetime.now(timezone.utc).isoformat())

    with destino.open("a", newline="", encoding="utf-8") as arquivo:
        csv.writer(arquivo).writerow(asdict(registro).values())

    return registro


def listar_contatos(vin: str, path: str | Path | None = None) -> list[ContatoRegistro]:
    """Histórico de contatos de um VIN, em ordem de registro. Lista vazia se nunca houve nenhum."""
    destino = Path(path if path is not None else CONTATOS_PATH)
    if not destino.exists():
        return []

    with destino.open(newline="", encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))

    return [
        ContatoRegistro(vin=linha["vin"], usuario=linha["usuario"], acao=linha["acao"], data=linha["data"])
        for linha in linhas
        if linha["vin"] == vin
    ]
