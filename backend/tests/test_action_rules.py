from src.domain.action_rules import LIMITE_ALTO, LIMITE_BAIXO, recomendar_acao


def test_score_baixo_recomenda_lembrete() -> None:
    assert recomendar_acao(0.0) == "lembrete"
    assert recomendar_acao(0.1) == "lembrete"


def test_score_medio_recomenda_oferta() -> None:
    assert recomendar_acao(0.5) == "oferta"


def test_score_alto_recomenda_contato_ativo() -> None:
    assert recomendar_acao(0.9) == "contato_ativo"
    assert recomendar_acao(1.0) == "contato_ativo"


def test_limite_baixo_e_inclusivo_no_lado_baixo() -> None:
    assert recomendar_acao(LIMITE_BAIXO) == "lembrete"


def test_logo_acima_do_limite_baixo_e_oferta() -> None:
    assert recomendar_acao(LIMITE_BAIXO + 0.01) == "oferta"


def test_limite_alto_e_inclusivo_no_lado_alto() -> None:
    assert recomendar_acao(LIMITE_ALTO) == "contato_ativo"


def test_logo_abaixo_do_limite_alto_e_oferta() -> None:
    assert recomendar_acao(LIMITE_ALTO - 0.01) == "oferta"


def test_limites_sao_parametrizaveis() -> None:
    assert recomendar_acao(0.5, limite_baixo=0.6, limite_alto=0.9) == "lembrete"


def test_exemplo_real_baixo_risco_ranger_223_dias() -> None:
    # VIN real de data/processed/leads.csv: RANGER, 223 dias sem serviço, score 0.0002.
    assert recomendar_acao(0.0002) == "lembrete"


def test_exemplo_real_risco_medio_ranger_293_dias() -> None:
    # VIN real: RANGER, 293 dias sem serviço, score 0.619.
    assert recomendar_acao(0.619) == "oferta"


def test_exemplo_real_alto_risco_ka_1016_dias() -> None:
    # VIN real: KA (modelo descontinuado), 1016 dias sem serviço, score 1.0.
    assert recomendar_acao(1.0) == "contato_ativo"
