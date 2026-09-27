import pandas as pd
import pytest
from fastapi.testclient import TestClient
from tests.conftest import auth_headers

from src.interfaces.api.main import app
from src.interfaces.api.routers import leads as leads_router
from src.interfaces.api.routers.leads import LIMIT_PADRAO

client = TestClient(app)


def _leads_teste() -> pd.DataFrame:
    # prioridade == score em todas as linhas: os testes que dependem da ordem/filtro
    # existentes continuam válidos (ordenar por prioridade dá o mesmo resultado que
    # ordenar por score aqui); o comportamento real de "prioridade pode divergir do
    # score" tem teste dedicado em test_leads_ordenacao_usa_prioridade_nao_so_score.
    linhas = [
        {"vin": "v1", "dealerCode": "100", "score": 0.9, "motivo": "motivo v1", "modelo": "RANGER", "diasSemServico": 400.0, "prioridade": 0.9},
        {"vin": "v2", "dealerCode": "100", "score": 0.3, "motivo": "motivo v2", "modelo": "KA", "diasSemServico": 90.0, "prioridade": 0.3},
        {"vin": "v3", "dealerCode": "200", "score": 0.8, "motivo": "motivo v3", "modelo": "RANGER", "diasSemServico": 250.0, "prioridade": 0.8},
        {"vin": "v4", "dealerCode": "200", "score": 0.1, "motivo": "motivo v4", "modelo": "ECOSPORT", "diasSemServico": 10.0, "prioridade": 0.1},
        # empatado com v1 em score/prioridade (0.9), mas com mais dias sem servico -> deve rankear antes.
        {"vin": "v5", "dealerCode": "100", "score": 0.9, "motivo": "motivo v5", "modelo": "RANGER", "diasSemServico": 800.0, "prioridade": 0.9},
    ]
    return pd.DataFrame(linhas)


@pytest.fixture(autouse=True)
def _dados_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: _leads_teste())


def test_leads_sem_filtro_retorna_todos_ordenados_por_prioridade_desc(token_gestor: str) -> None:
    resposta = client.get("/api/leads", headers=auth_headers(token_gestor))
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert [linha["vin"] for linha in corpo["leads"]] == ["v5", "v1", "v3", "v2", "v4"]
    prioridades = [linha["prioridade"] for linha in corpo["leads"]]
    assert prioridades == sorted(prioridades, reverse=True)


def test_leads_empate_de_prioridade_desempata_por_dias_sem_servico(token_gestor: str) -> None:
    # v1 e v5 empatados em prioridade 0.9 — sem desempate, a ordem entre eles seria
    # arbitraria (a ordem de geracao do CSV); com diasSemServico, o VIN ha mais
    # tempo sem servico vem primeiro.
    resposta = client.get("/api/leads", headers=auth_headers(token_gestor))
    corpo = resposta.json()["leads"]

    assert corpo[0]["vin"] == "v5"
    assert corpo[1]["vin"] == "v1"
    assert corpo[0]["prioridade"] == corpo[1]["prioridade"] == 0.9
    assert corpo[0]["diasSemServico"] > corpo[1]["diasSemServico"]


def test_leads_ordenacao_usa_prioridade_nao_so_score(monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    # va tem score maior, mas vb tem prioridade maior (mais valor de cliente por
    # tras) — a fila deve respeitar prioridade, nao score bruto.
    leads_com_prioridade_divergente = pd.DataFrame([
        {"vin": "va", "dealerCode": "100", "score": 0.9, "motivo": "m", "modelo": "RANGER", "diasSemServico": 100.0, "prioridade": 0.5},
        {"vin": "vb", "dealerCode": "100", "score": 0.5, "motivo": "m", "modelo": "RANGER", "diasSemServico": 100.0, "prioridade": 0.9},
    ])
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: leads_com_prioridade_divergente)

    resposta = client.get("/api/leads", headers=auth_headers(token_gestor))
    corpo = resposta.json()["leads"]

    assert [linha["vin"] for linha in corpo] == ["vb", "va"]


def test_leads_devolve_vin_score_motivo_concessionaria_modelo_dias_e_prioridade(token_gestor: str) -> None:
    resposta = client.get("/api/leads", headers=auth_headers(token_gestor))
    primeiro = resposta.json()["leads"][0]

    assert set(primeiro.keys()) == {
        "vin", "dealerCode", "score", "motivo", "modelo", "diasSemServico", "prioridade",
    }
    assert primeiro == {
        "vin": "v5", "dealerCode": "100", "score": 0.9, "motivo": "motivo v5",
        "modelo": "RANGER", "diasSemServico": 800.0, "prioridade": 0.9,
    }


def test_leads_filtro_concessionaria_restringe_e_mantem_ordem(token_gestor: str) -> None:
    resposta = client.get("/api/leads", params={"concessionaria": "200"}, headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert [linha["vin"] for linha in corpo["leads"]] == ["v3", "v4"]
    assert all(linha["dealerCode"] == "200" for linha in corpo["leads"])
    assert corpo["total"] == 2


def test_leads_concessionaria_sem_correspondencia_retorna_lista_vazia(token_gestor: str) -> None:
    resposta = client.get("/api/leads", params={"concessionaria": "999999"}, headers=auth_headers(token_gestor))
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["leads"] == []
    assert corpo["total"] == 0


def test_leads_pagina_traz_o_tamanho_de_pagina_pedido(monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    muitos_leads = pd.DataFrame([
        {
            "vin": f"v{i}", "dealerCode": "100", "score": i / 1000, "motivo": "m",
            "modelo": "RANGER", "diasSemServico": float(i), "prioridade": i / 1000,
        }
        for i in range(200)
    ])
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: muitos_leads)

    resposta = client.get("/api/leads", headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert len(corpo["leads"]) == LIMIT_PADRAO
    assert corpo["total"] == 200
    assert corpo["pagina"] == 1
    assert corpo["tamanhoPagina"] == LIMIT_PADRAO
    assert corpo["leads"][0]["vin"] == "v199"  # maior score
    assert corpo["leads"][-1]["vin"] == "v150"  # 50-esimo maior


def test_leads_segunda_pagina_traz_os_proximos_leads(monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    muitos_leads = pd.DataFrame([
        {
            "vin": f"v{i}", "dealerCode": "100", "score": i / 1000, "motivo": "m",
            "modelo": "RANGER", "diasSemServico": float(i), "prioridade": i / 1000,
        }
        for i in range(200)
    ])
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: muitos_leads)

    resposta = client.get("/api/leads", params={"pagina": 2}, headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert corpo["pagina"] == 2
    assert len(corpo["leads"]) == LIMIT_PADRAO
    assert corpo["leads"][0]["vin"] == "v149"  # 51-esimo maior
    assert corpo["leads"][-1]["vin"] == "v100"  # 100-esimo maior


def test_leads_pagina_alem_do_total_retorna_lista_vazia_sem_erro(monkeypatch: pytest.MonkeyPatch, token_gestor: str) -> None:
    muitos_leads = pd.DataFrame([
        {
            "vin": f"v{i}", "dealerCode": "100", "score": i / 1000, "motivo": "m",
            "modelo": "RANGER", "diasSemServico": float(i), "prioridade": i / 1000,
        }
        for i in range(10)
    ])
    monkeypatch.setattr(leads_router, "load_leads_data", lambda: muitos_leads)

    resposta = client.get("/api/leads", params={"pagina": 5}, headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo["leads"] == []
    assert corpo["total"] == 10


def test_leads_tamanho_pagina_customizado(token_gestor: str) -> None:
    resposta = client.get("/api/leads", params={"tamanhoPagina": 2}, headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert len(corpo["leads"]) == 2
    assert corpo["tamanhoPagina"] == 2
    assert corpo["total"] == 5


def test_leads_score_minimo_filtra_leads_de_risco_baixo(token_gestor: str) -> None:
    # so' v1, v3 e v5 tem score >= 0.5 (v2=0.3, v4=0.1) — o piso e' o que permite
    # a fila trazer leads fora do topo empatado, sem depender so' da pagina.
    resposta = client.get("/api/leads", params={"scoreMinimo": 0.5}, headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert {linha["vin"] for linha in corpo["leads"]} == {"v1", "v3", "v5"}
    assert corpo["total"] == 3


def test_leads_score_minimo_fora_do_intervalo_retorna_422(token_gestor: str) -> None:
    resposta = client.get("/api/leads", params={"scoreMinimo": 1.5}, headers=auth_headers(token_gestor))
    assert resposta.status_code == 422


def test_leads_score_maximo_filtra_leads_de_risco_alto(token_gestor: str) -> None:
    # so' v2 e v4 tem score < 0.7 (v1=0.9, v3=0.8, v5=0.9) — o teto e' o que
    # isola a banda "media" sem trazer os leads de risco alto junto.
    resposta = client.get("/api/leads", params={"scoreMaximo": 0.7}, headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert {linha["vin"] for linha in corpo["leads"]} == {"v2", "v4"}
    assert corpo["total"] == 2


def test_leads_score_minimo_e_maximo_isolam_uma_banda_exclusiva_do_topo(token_gestor: str) -> None:
    # v3 (score 0.8) fica de fora: scoreMinimo=0.3 e scoreMaximo=0.8 e' a banda
    # "media" da tela — [0.3, 0.8) — sem os leads de risco alto empatados no teto.
    resposta = client.get("/api/leads", params={"scoreMinimo": 0.3, "scoreMaximo": 0.8}, headers=auth_headers(token_gestor))
    corpo = resposta.json()

    assert {linha["vin"] for linha in corpo["leads"]} == {"v2"}
    assert corpo["total"] == 1


def test_leads_score_maximo_fora_do_intervalo_retorna_422(token_gestor: str) -> None:
    resposta = client.get("/api/leads", params={"scoreMaximo": 1.5}, headers=auth_headers(token_gestor))
    assert resposta.status_code == 422


def test_leads_query_param_desconhecido_e_ignorado(token_gestor: str) -> None:
    resposta = client.get("/api/leads", params={"paramInexistente": "qualquer-coisa"}, headers=auth_headers(token_gestor))
    assert resposta.status_code == 200


def test_leads_arquivo_de_dados_ausente_nao_derruba_o_processo(token_gestor: str) -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError(
            "Lista de leads não encontrada. Rode `python -m src.interfaces.pipeline.generate_leads`."
        )

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(leads_router, "load_leads_data", _sem_dados)
        resposta = client_sem_raise.get("/api/leads", headers=auth_headers(token_gestor))

    assert resposta.status_code == 500

    resposta_seguinte = client.get("/api/leads", headers=auth_headers(token_gestor))
    assert resposta_seguinte.status_code == 200


# --------------------------------------------------------------------------- #
# GET /api/leads/distribuicao-score                                            #
# --------------------------------------------------------------------------- #

def test_distribuicao_score_retorna_todas_as_faixas_somando_o_total(token_gestor: str) -> None:
    resposta = client.get("/api/leads/distribuicao-score", headers=auth_headers(token_gestor))
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert len(corpo) == 10
    assert sum(f["quantidade"] for f in corpo) == 5  # os 5 leads de _leads_teste()
    assert all(set(f.keys()) == {"faixaInicio", "faixaFim", "quantidade"} for f in corpo)


def test_distribuicao_score_arquivo_de_dados_ausente_nao_derruba_o_processo(token_gestor: str) -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError("Lista de leads não encontrada.")

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(leads_router, "load_leads_data", _sem_dados)
        resposta = client_sem_raise.get("/api/leads/distribuicao-score", headers=auth_headers(token_gestor))

    assert resposta.status_code == 500

    resposta_seguinte = client.get("/api/leads/distribuicao-score", headers=auth_headers(token_gestor))
    assert resposta_seguinte.status_code == 200


# --------------------------------------------------------------------------- #
# GET /api/leads/{vin}/acao                                                    #
# --------------------------------------------------------------------------- #

def test_acao_recomendada_score_alto_e_contato_ativo(token_gestor: str) -> None:
    resposta = client.get("/api/leads/v1/acao", headers=auth_headers(token_gestor))  # score 0.9, 400 dias sem servico
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert corpo["acao"] == "contato_ativo"
    assert "RANGER" in corpo["mensagem"]
    assert "400 dias" in corpo["mensagem"]


def test_acao_recomendada_score_medio_e_oferta(token_gestor: str) -> None:
    resposta = client.get("/api/leads/v2/acao", headers=auth_headers(token_gestor))  # score 0.3, 90 dias sem servico
    corpo = resposta.json()

    assert corpo["acao"] == "oferta"
    assert "KA" in corpo["mensagem"]
    assert "90 dias" in corpo["mensagem"]


def test_acao_recomendada_score_baixo_e_lembrete(token_gestor: str) -> None:
    resposta = client.get("/api/leads/v4/acao", headers=auth_headers(token_gestor))  # score 0.1, 10 dias sem servico
    corpo = resposta.json()

    assert corpo["acao"] == "lembrete"
    assert "ECOSPORT" in corpo["mensagem"]
    assert "10 dias" in corpo["mensagem"]


def test_acao_recomendada_devolve_exatamente_acao_e_mensagem(token_gestor: str) -> None:
    resposta = client.get("/api/leads/v3/acao", headers=auth_headers(token_gestor))
    assert set(resposta.json().keys()) == {"acao", "mensagem"}


def test_acao_recomendada_vin_inexistente_retorna_404(token_gestor: str) -> None:
    resposta = client.get("/api/leads/vin-que-nao-existe/acao", headers=auth_headers(token_gestor))
    assert resposta.status_code == 404
    assert "vin-que-nao-existe" in resposta.json()["detail"]


def test_acao_recomendada_arquivo_de_dados_ausente_nao_derruba_o_processo(token_gestor: str) -> None:
    def _sem_dados() -> pd.DataFrame:
        raise FileNotFoundError("Lista de leads não encontrada.")

    client_sem_raise = TestClient(app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(leads_router, "load_leads_data", _sem_dados)
        resposta = client_sem_raise.get("/api/leads/v1/acao", headers=auth_headers(token_gestor))

    assert resposta.status_code == 500

    resposta_seguinte = client.get("/api/leads/v1/acao", headers=auth_headers(token_gestor))
    assert resposta_seguinte.status_code == 200
