from app.services.text_utils import TextoBusca, normalizar, remover_dados_pessoais, trecho


def test_normalizar_remove_acentos_e_espacos():
    assert normalizar("  Experiência   em   Gestão ") == "experiencia em gestao"


def test_busca_ignora_acentos_e_maiusculas_e_preserva_o_trecho_original():
    busca = TextoBusca("Liderança de equipes e Comunicação clara")
    m = busca.buscar("comunicacao")
    assert m is not None
    assert busca.termo_original(m) == "Comunicação"


def test_busca_respeita_fronteiras_de_termos_com_simbolos():
    assert TextoBusca("Experiência com C++ e C#").buscar("c++")
    assert TextoBusca("Experiência com C# e .NET").buscar("c#")
    assert not TextoBusca("javascript").buscar("java")
    assert not TextoBusca("reactivo").buscar("react")


def test_sinonimo_sensivel_a_maiusculas_evita_falso_positivo():
    assert TextoBusca("Backend em Go e Python").buscar("=Go")
    assert not TextoBusca("Participei do go live do sistema").buscar("=Go")


def test_termo_composto_aceita_quebra_de_linha():
    assert TextoBusca("trabalho em\nequipe").buscar("trabalho em equipe")


def test_remove_contato_documentos_e_caracteristicas_pessoais():
    texto = (
        "Maria Teste\nmaria@exemplo.com | (21) 99876-5432 | CPF 123.456.789-09\n"
        "Data de nascimento: 01/01/1990\nEstado civil: casada\nCasada, 35 anos\nCEP 01234-567\n"
        "5 anos de experiência com Python\nmar/2019 - 2021"
    )
    limpo = remover_dados_pessoais(texto)
    for dado in ("maria@exemplo.com", "99876-5432", "123.456.789-09", "01/01/1990", "casada", "Casada", "01234-567"):
        assert dado not in limpo
    assert "Maria Teste" in limpo  # o nome continua (é exibido ao usuário, mas não entra na análise)
    assert "5 anos de experiência com Python" in limpo
    assert "mar/2019 - 2021" in limpo


def test_trecho_fica_restrito_a_linha_do_termo():
    texto = "Linha anterior\nDesenvolvi APIs em Python com FastAPI.\nLinha seguinte"
    i = texto.index("Python")
    resultado = trecho(texto, i, i + 6)
    assert resultado == "Desenvolvi APIs em Python com FastAPI."
