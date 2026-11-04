from app.core.config import Settings
from app.services.ai_service import (
    ContextoVaga,
    ErroProvedorIA,
    ProvedorLocal,
    ServicoIA,
    obter_provedor,
    verificar_veracidade,
)
from app.services.job_analyzer import analisar_vaga
from app.services.matching_engine import calcular_compatibilidade
from app.services.resume_analyzer import analisar_curriculo
from tests.conftest import HOJE
from tests.fixtures import CURRICULO_DEV_PYTHON, VAGA_BACKEND


def _contexto(motor):
    cv = analisar_curriculo(CURRICULO_DEV_PYTHON, HOJE)
    return calcular_compatibilidade(cv, analisar_vaga(VAGA_BACKEND), motor), cv


def test_sugestoes_locais_apontam_lacunas_reais(motor):
    resultado, cv = _contexto(motor)
    sugestoes = ProvedorLocal().gerar_sugestoes(resultado, cv)
    assert sugestoes
    obrigatorios = next(s for s in sugestoes if s.titulo == "Requisitos obrigatórios não encontrados")
    assert "Kubernetes" in obrigatorios.descricao
    assert "Se não tem, não inclua" in obrigatorios.descricao
    listadas = next(s for s in sugestoes if s.titulo.startswith("Mostre onde"))
    assert "Comunicação" in listadas.descricao


def test_sugestoes_locais_sao_deterministicas(motor):
    resultado, cv = _contexto(motor)
    assert ProvedorLocal().gerar_sugestoes(resultado, cv) == ProvedorLocal().gerar_sugestoes(resultado, cv)


def test_reescrita_local_troca_responsavel_por_verbo_de_acao():
    texto = "• Responsável por desenvolver APIs em Python\n• Fui responsável pela manutenção do sistema\n• Eu fazer deploys"
    r = ProvedorLocal().reescrever("experiencia", texto, None)
    linhas = r.texto.splitlines()
    assert linhas[0] == "• Desenvolvi APIs em Python"
    assert linhas[1] == "• Responsável pela manutenção do sistema"


def test_reescrita_local_junta_linhas_quebradas_pelo_pdf():
    texto = "• Implementei testes automatizados com pytest e\nreduzi falhas em produção.\n• Configurei CI/CD."
    r = ProvedorLocal().reescrever("experiencia", texto, None)
    assert r.texto.splitlines()[0] == "• Implementei testes automatizados com pytest e reduzi falhas em produção."


def test_reescrita_local_nao_junta_periodo_a_linha_do_cargo():
    texto = "Desenvolvedora Júnior — Loja Exemplo\njan/2019 – fev/2021\n• Mantive aplicações Django."
    r = ProvedorLocal().reescrever("experiencia", texto, None)
    assert r.texto.splitlines()[:2] == ["Desenvolvedora Júnior — Loja Exemplo", "Jan/2019 – fev/2021"]


def test_sugestao_de_metricas_usa_item_descritivo_como_exemplo(motor):
    resultado, cv = _contexto(motor)
    sugestoes = ProvedorLocal().gerar_sugestoes(resultado, cv)
    metricas = [s for s in sugestoes if s.titulo == "Adicione resultados mensuráveis"]
    for s in metricas:
        assert "Empresa Fictícia" not in s.descricao


def test_reescrita_de_competencias_agrupa_e_padroniza_sem_perder_termos():
    r = ProvedorLocal().reescrever("competencias", "python, postgres, docker, comunicação, Cobol avançado", None)
    assert "Linguagens: Python" in r.texto
    assert "PostgreSQL" in r.texto
    assert "Cobol avançado" in r.texto  # fora do catálogo, mas mantido


def test_resumo_recebe_observacoes_da_vaga():
    vaga = ContextoVaga(cargo="Desenvolvedora Back-end", competencias_atendidas=["FastAPI", "PostgreSQL"], termos_vaga=[])
    r = ProvedorLocal().reescrever("resumo", "Eu sou desenvolvedora com foco em Python.", vaga)
    assert r.texto == "Sou desenvolvedora com foco em Python."
    assert any("FastAPI" in o for o in r.observacoes)


def test_verificacao_de_veracidade_aponta_competencias_e_numeros_novos():
    alertas = verificar_veracidade("Desenvolvi APIs em Python.", "Desenvolvi APIs em Python e Kubernetes, reduzindo 40% do tempo.")
    assert any("Kubernetes" in a for a in alertas)
    assert any("40%" in a for a in alertas)
    assert verificar_veracidade("Desenvolvi APIs em Python.", "Desenvolvi APIs REST em Python.") == [
        "Atenção: a sugestão cita REST, que não aparece(m) no texto original. Mantenha apenas se corresponder à sua experiência real."
    ]


class _ProvedorQueFalha:
    nome = "falho"

    def gerar_sugestoes(self, resultado, curriculo):
        raise ErroProvedorIA("sem rede")

    def reescrever(self, secao, texto, vaga):
        raise ErroProvedorIA("sem rede")


def test_servico_volta_para_o_modo_local_quando_o_provedor_falha(motor):
    resultado, cv = _contexto(motor)
    servico = ServicoIA(_ProvedorQueFalha())
    sugestoes, fonte, aviso = servico.sugestoes(resultado, cv)
    assert sugestoes and fonte == "local" and "falho" in aviso
    reescrita, fonte = servico.reescrever("resumo", "Responsável por criar relatórios.", None)
    assert fonte == "local"
    assert reescrita.texto == "Criei relatórios."


def test_escolha_do_provedor():
    assert obter_provedor(Settings(ai_provider="auto", gemini_api_key="")).nome == "local"
    assert obter_provedor(Settings(ai_provider="gemini", gemini_api_key="")).nome == "local"
    assert obter_provedor(Settings(ai_provider="local", gemini_api_key="chave")).nome == "local"
    assert obter_provedor(Settings(ai_provider="auto", gemini_api_key="chave-de-teste")).nome == "gemini"
