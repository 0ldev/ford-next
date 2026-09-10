from src.domain.message_templates import CONCESSIONARIA_PADRAO, montar_mensagem


def test_lembrete_cita_modelo_e_dias() -> None:
    mensagem = montar_mensagem("lembrete", modelo="ECOSPORT", dias_sem_servico=90, concessionaria="Concessionária Sul")

    assert "ECOSPORT" in mensagem
    assert "90 dias" in mensagem
    assert "Concessionária Sul" in mensagem


def test_oferta_cita_modelo_e_dias() -> None:
    mensagem = montar_mensagem("oferta", modelo="KA", dias_sem_servico=250, concessionaria="Concessionária Norte")

    assert "KA" in mensagem
    assert "250 dias" in mensagem


def test_contato_ativo_cita_modelo_e_dias() -> None:
    mensagem = montar_mensagem("contato_ativo", modelo="RANGER", dias_sem_servico=400, concessionaria="Concessionária Oeste")

    assert "RANGER" in mensagem
    assert "400 dias" in mensagem


def test_os_tres_templates_tem_tom_diferente() -> None:
    kwargs = dict(modelo="KA", dias_sem_servico=200, concessionaria="Concessionária Teste")

    lembrete = montar_mensagem("lembrete", **kwargs)
    oferta = montar_mensagem("oferta", **kwargs)
    contato = montar_mensagem("contato_ativo", **kwargs)

    assert lembrete != oferta != contato


def test_nenhum_template_menciona_score_ou_risco() -> None:
    # O score/rótulo de risco e informacao interna, nao deve vazar para o cliente.
    for acao in ("lembrete", "oferta", "contato_ativo"):
        mensagem = montar_mensagem(acao, modelo="KA", dias_sem_servico=100).lower()
        assert "score" not in mensagem
        assert "risco" not in mensagem


def test_dias_e_arredondado_para_inteiro() -> None:
    mensagem = montar_mensagem("lembrete", modelo="KA", dias_sem_servico=180.6)
    assert "181 dias" in mensagem


def test_concessionaria_padrao_quando_nao_informada() -> None:
    mensagem = montar_mensagem("lembrete", modelo="KA", dias_sem_servico=100)
    assert CONCESSIONARIA_PADRAO in mensagem


def test_exemplo_real_baixo_risco_ranger_223_dias() -> None:
    # VIN real de data/processed/leads.csv: RANGER, 223 dias sem serviço, score 0.0002
    # (risco baixo -> "lembrete", ver test_action_rules.py).
    mensagem = montar_mensagem("lembrete", modelo="RANGER", dias_sem_servico=223)

    assert mensagem == (
        "Olá! Notamos que já faz 223 dias desde a última revisão do seu RANGER "
        "na sua concessionária Ford. Que tal agendar uma manutenção preventiva "
        "quando for conveniente para você?"
    )


def test_exemplo_real_risco_medio_ranger_293_dias() -> None:
    # VIN real: RANGER, 293 dias sem serviço, score 0.619 (risco médio -> "oferta").
    mensagem = montar_mensagem("oferta", modelo="RANGER", dias_sem_servico=293, concessionaria="concessionária 1009")

    assert "RANGER" in mensagem
    assert "293 dias" in mensagem
    assert "concessionária 1009" in mensagem


def test_exemplo_real_alto_risco_ka_1016_dias() -> None:
    # VIN real: KA (modelo descontinuado), 1016 dias sem serviço, score 1.0 (risco alto).
    mensagem = montar_mensagem("contato_ativo", modelo="KA", dias_sem_servico=1016, concessionaria="concessionária 100")

    assert "KA" in mensagem
    assert "1016 dias" in mensagem
    assert "concessionária 100" in mensagem
