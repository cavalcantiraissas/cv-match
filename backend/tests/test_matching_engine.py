import pytest

from app.core.config import PESOS_CATEGORIAS
from app.services.job_analyzer import analisar_vaga
from app.services.matching_engine import calcular_compatibilidade, classificar, pontuar_itens
from app.services.resume_analyzer import analisar_curriculo
from app.services.text_utils import remover_dados_pessoais
from tests.conftest import HOJE
from tests.fixtures import CURRICULO_DEV_PYTHON, CURRICULO_MARKETING, VAGA_BACKEND, VAGA_SEM_SECOES


def _analisar(cv_texto, vaga_texto, motor):
    cv = analisar_curriculo(remover_dados_pessoais(cv_texto), HOJE)
    return calcular_compatibilidade(cv, analisar_vaga(vaga_texto), motor)


def test_pesos_somam_100_por_cento():
    assert sum(PESOS_CATEGORIAS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("score,esperado", [
    (100, "Excelente compatibilidade"), (90, "Excelente compatibilidade"), (89, "Boa compatibilidade"),
    (75, "Boa compatibilidade"), (74, "Compatibilidade moderada"), (60, "Compatibilidade moderada"),
    (59, "Baixa compatibilidade"), (40, "Baixa compatibilidade"), (39, "Compatibilidade muito baixa"),
    (0, "Compatibilidade muito baixa"),
])
def test_faixas_de_classificacao(score, esperado):
    assert classificar(score) == esperado


def test_desejaveis_nunca_reduzem_o_score_da_categoria():
    so_obrigatorios = pontuar_itens([(1.0, True), (0.0, True)])
    assert pontuar_itens([(1.0, True), (0.0, True), (0.0, False)]) == so_obrigatorios
    assert pontuar_itens([(1.0, True), (0.0, True), (1.0, False)]) > so_obrigatorios


def test_categoria_so_com_desejaveis_nao_e_aplicavel():
    assert pontuar_itens([(0.0, False), (1.0, False)]) is None
    assert pontuar_itens([]) is None


def test_curriculo_aderente_tem_score_alto(motor):
    r = _analisar(CURRICULO_DEV_PYTHON, VAGA_BACKEND, motor)
    assert r.score >= 75


def test_curriculo_de_outra_area_tem_score_baixo(motor):
    r = _analisar(CURRICULO_MARKETING, VAGA_BACKEND, motor)
    assert r.score < 40


def test_score_e_reproduzivel(motor):
    a = _analisar(CURRICULO_DEV_PYTHON, VAGA_BACKEND, motor)
    b = _analisar(CURRICULO_DEV_PYTHON, VAGA_BACKEND, motor)
    assert a.score == b.score
    assert [c.score for c in a.categorias] == [c.score for c in b.categorias]
    assert [r.status for r in a.requisitos] == [r.status for r in b.requisitos]


def test_score_e_a_soma_das_contribuicoes(motor):
    r = _analisar(CURRICULO_DEV_PYTHON, VAGA_BACKEND, motor)
    assert r.score == round(sum(c.contribuicao for c in r.categorias))
    assert sum(c.peso_efetivo for c in r.categorias) == pytest.approx(1.0, abs=1e-3)


def test_pesos_redistribuidos_quando_vaga_nao_tem_a_categoria(motor):
    r = _analisar(CURRICULO_DEV_PYTHON, VAGA_SEM_SECOES, motor)
    por_chave = {c.chave: c for c in r.categorias}
    assert not por_chave["formacao"].aplicavel
    assert por_chave["formacao"].peso_efetivo == 0
    assert por_chave["competencias_tecnicas"].peso_efetivo == pytest.approx(0.30 / 0.70, abs=1e-3)


def test_todo_requisito_tem_status_e_justificativa(motor):
    r = _analisar(CURRICULO_DEV_PYTHON, VAGA_BACKEND, motor)
    assert r.requisitos
    for req in r.requisitos:
        assert req.status in ("atendido", "parcial", "nao_identificado")
        assert req.justificativa


def test_status_dos_requisitos_sao_justificados_pelo_curriculo(motor):
    r = _analisar(CURRICULO_DEV_PYTHON, VAGA_BACKEND, motor)
    por_texto = {q.texto: q for q in r.requisitos}
    postgres = por_texto["Conhecimento em PostgreSQL."]
    assert postgres.status == "atendido"
    assert "PostgreSQL" in postgres.trecho
    assert por_texto["Experiência com Docker e Kubernetes."].status == "parcial"
    assert por_texto["Conhecimento em Terraform."].status == "nao_identificado"


def test_competencia_apenas_listada_e_parcial(motor):
    r = _analisar(CURRICULO_DEV_PYTHON, VAGA_BACKEND, motor)
    comunicacao = next(c for c in r.competencias if c.nome == "Comunicação")
    assert comunicacao.status == "parcial"
    assert comunicacao.evidencia == "listada"


def test_tecnologia_equivalente_conta_como_relacionada(motor):
    vaga = "Vaga: Dev Back-end\nRequisitos:\n- Experiência com Flask\n- Experiência com MongoDB\n- Python"
    r = _analisar(CURRICULO_DEV_PYTHON, vaga, motor)
    flask = next(c for c in r.competencias if c.nome == "Flask")
    assert flask.evidencia == "relacionada"  # o currículo tem FastAPI e Django
    assert "FastAPI" in flask.justificativa or "Django" in flask.justificativa
    mongo = next(c for c in r.competencias if c.nome == "MongoDB")
    assert mongo.evidencia == "ausente"


def test_ats_detecta_variacao_de_termo(motor):
    vaga = "Vaga: Dev\nRequisitos:\n- Experiência com Postgres\n- Python"
    r = _analisar(CURRICULO_DEV_PYTHON, vaga, motor)
    postgres = next(p for p in r.palavras_chave if p.termo == "PostgreSQL")
    assert postgres.status == "variacao"
    assert "Postgres" in postgres.sugestao


def test_dados_pessoais_nao_alteram_o_score(motor):
    base = _analisar(CURRICULO_DEV_PYTHON, VAGA_BACKEND, motor)
    extra = CURRICULO_DEV_PYTHON.replace(
        "Data de nascimento: 12/03/1994",
        "Data de nascimento: 01/01/1960\nSexo: feminino\nEstado civil: casada\nEndereço: Rua Fictícia, 100",
    )
    com_dados = _analisar(extra, VAGA_BACKEND, motor)
    assert com_dados.score == base.score


def test_vaga_sem_requisitos_identificaveis(motor):
    r = _analisar(CURRICULO_DEV_PYTHON, "Somos uma empresa incrível.\nVenha crescer conosco em um ambiente leve.", motor)
    assert r.score == 0
    assert any("requisitos obrigatórios" in a for a in r.avisos)
