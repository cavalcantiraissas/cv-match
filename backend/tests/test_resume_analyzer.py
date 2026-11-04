from datetime import date

from app.services.resume_analyzer import (
    analisar_curriculo,
    calcular_experiencia,
    detectar_formacao,
    detectar_idiomas,
    identificar_secoes,
)
from tests.conftest import HOJE
from tests.fixtures import CURRICULO_DEV_PYTHON, CURRICULO_MARKETING


def test_identifica_secoes_do_curriculo():
    chaves = [s.chave for s in identificar_secoes(CURRICULO_DEV_PYTHON)]
    assert chaves == ["informacoes", "resumo", "experiencia", "formacao", "competencias", "idiomas", "certificacoes"]


def test_titulos_em_ingles_e_com_dois_pontos():
    texto = "John Doe\nSummary\nBackend developer.\nWork Experience\nDeveloper at X\nSkills: Python, SQL\nProjects\nAPI"
    secoes = {s.chave: s.texto for s in identificar_secoes(texto)}
    assert secoes["competencias"] == "Python, SQL"
    assert set(secoes) == {"informacoes", "resumo", "experiencia", "competencias", "projetos"}


def test_curriculo_sem_titulos_vira_secao_geral():
    secoes = identificar_secoes("Texto corrido sem nenhum título de seção reconhecível.\nOutra linha.")
    assert [s.chave for s in secoes] == ["geral"]


def test_forca_da_evidencia_depende_da_secao():
    cv = analisar_curriculo(CURRICULO_DEV_PYTHON, HOJE)
    assert cv.competencias["FastAPI"].nivel == "forte"  # usada em experiência
    assert cv.competencias["Linux"].nivel == "listada"  # só na lista de competências
    assert cv.competencias["Comunicação"].nivel == "listada"
    assert "FastAPI" in cv.competencias["FastAPI"].trecho


def test_competencia_comprovada_por_outra():
    cv = analisar_curriculo(CURRICULO_DEV_PYTHON, HOJE)
    assert cv.competencias["SQL"].nivel == "forte"
    assert cv.competencias["Metodologias ágeis"].inferida_de == "Scrum"


def test_secao_de_contato_nao_conta_como_evidencia():
    texto = "Fulano\nPython Developer | github.com/fulano\n\nEXPERIÊNCIA\nAnalista financeiro em banco, 2018 - 2020"
    cv = analisar_curriculo(texto, HOJE)
    assert "Python" not in cv.competencias


def test_soma_periodos_sem_contar_sobreposicao_duas_vezes():
    texto = "Empresa A\njan/2018 - dez/2019\nEmpresa B (paralelo)\njun/2019 - dez/2020\nEmpresa C\n01/2022 - atual"
    anos, periodos = calcular_experiencia(texto, date(2023, 12, 1))
    # 2018-01..2020-12 = 36 meses; 2022-01..2023-12 = 24 meses -> 60 meses
    assert anos == 5.0
    assert len(periodos) == 3


def test_periodos_em_ingles_e_por_extenso():
    anos, _ = calcular_experiencia("Company\nJan 2020 to Present\nOutra\nmarço de 2017 a dezembro de 2019", date(2024, 12, 1))
    assert anos == 7.8


def test_experiencia_calculada_no_curriculo_completo():
    cv = analisar_curriculo(CURRICULO_DEV_PYTHON, HOJE)
    assert cv.anos_experiencia == 7.9


def test_formacao_concluida_e_em_andamento():
    concluida = detectar_formacao("Bacharelado em Ciência da Computação\n2014 - 2018")
    assert (concluida.nivel, concluida.nivel_concluido, concluida.em_andamento) == (3, 3, False)
    assert concluida.areas == ["Ciência da Computação"]

    cursando = detectar_formacao("Engenharia de Software - cursando (previsão de conclusão 2027)\nTécnico em Informática")
    assert cursando.nivel == 3 and cursando.em_andamento
    assert cursando.nivel_concluido == 2


def test_idiomas_com_nivel():
    idiomas = detectar_idiomas("Inglês - fluente\nEspanhol: intermediário\nFrancês")
    assert idiomas["Inglês"].nivel == 4
    assert idiomas["Espanhol"].nivel == 2
    assert idiomas["Francês"].nivel is None


def test_certificacoes():
    cv = analisar_curriculo(CURRICULO_DEV_PYTHON, HOJE)
    assert "AWS Certified" in cv.certificacoes


def test_curriculo_de_outra_area():
    cv = analisar_curriculo(CURRICULO_MARKETING, HOJE)
    assert "Marketing digital" in cv.competencias
    assert "Python" not in cv.competencias
    assert cv.formacao.areas == ["Marketing e Comunicação"]
