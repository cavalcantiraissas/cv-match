from app.services.job_analyzer import analisar_vaga
from tests.fixtures import VAGA_BACKEND, VAGA_SEM_SECOES


def _requisito(vaga, trecho):
    return next(r for r in vaga.requisitos if trecho in r.texto)


def test_cargo_e_nivel():
    vaga = analisar_vaga(VAGA_BACKEND)
    assert vaga.cargo == "Pessoa Desenvolvedora Back-end Python Pleno"
    assert vaga.nivel == "Pleno"


def test_titulo_da_vaga_nao_vira_requisito():
    vaga = analisar_vaga(VAGA_BACKEND)
    assert all("Pessoa Desenvolvedora" not in r.texto for r in vaga.requisitos)


def test_separa_obrigatorios_de_desejaveis():
    vaga = analisar_vaga(VAGA_BACKEND)
    assert _requisito(vaga, "PostgreSQL").obrigatorio
    assert not _requisito(vaga, "Terraform").obrigatorio
    assert vaga.competencias["Kubernetes"].obrigatoria
    assert not vaga.competencias["AWS"].obrigatoria


def test_tecnologia_citada_so_nas_responsabilidades_e_desejavel():
    vaga = analisar_vaga(VAGA_BACKEND)
    assert not vaga.competencias["Kafka"].obrigatoria
    assert vaga.competencias["Kafka"].origem == "responsabilidades"
    assert any("Kafka" in r for r in vaga.responsabilidades)


def test_beneficios_e_sobre_a_empresa_sao_ignorados():
    vaga = analisar_vaga(VAGA_BACKEND)
    textos = " ".join(r.texto for r in vaga.requisitos)
    assert "plano de saúde" not in textos
    assert "fintech" not in textos


def test_classifica_tipos_de_requisito():
    vaga = analisar_vaga(VAGA_BACKEND)
    assert _requisito(vaga, "3+ anos").tipo == "experiencia"
    assert _requisito(vaga, "3+ anos").anos == 3
    assert _requisito(vaga, "Formação superior").tipo == "formacao"
    assert _requisito(vaga, "Inglês").tipo == "idioma"
    assert _requisito(vaga, "Certificação AWS").tipo == "certificacao"
    assert _requisito(vaga, "comunicação").tipo == "comportamental"
    assert _requisito(vaga, "FastAPI ou Django").alternativas


def test_extrai_experiencia_formacao_e_idiomas():
    vaga = analisar_vaga(VAGA_BACKEND)
    assert vaga.anos_experiencia == 3
    assert vaga.formacao["nivel"] == 3
    assert vaga.formacao["afins"]
    assert vaga.formacao["areas"] == ["Ciência da Computação"]
    assert vaga.idiomas == {"Inglês": (2, True)}


def test_palavras_chave_guardam_o_termo_exato_da_vaga():
    vaga = analisar_vaga("Vaga: Dev\nRequisitos:\n- Experiência com Postgres e k8s")
    termos = {p.nome: p.termo for p in vaga.palavras_chave}
    assert termos == {"PostgreSQL": "Postgres", "Kubernetes": "k8s"}


def test_vaga_sem_secoes_trata_itens_como_obrigatorios_exceto_marcados():
    vaga = analisar_vaga(VAGA_SEM_SECOES)
    assert not vaga.estruturada
    assert vaga.nivel == "Júnior"
    assert vaga.competencias["SQL"].obrigatoria
    assert vaga.competencias["Power BI"].obrigatoria
    assert not _requisito(vaga, "Inglês avançado").obrigatorio


def test_item_curto_com_palavra_de_titulo_nao_vira_titulo():
    vaga = analisar_vaga("Vaga: Analista\nRequisitos:\nHabilidades de comunicação\nPerfil analítico\nDiferenciais:\nExcel")
    assert _requisito(vaga, "Habilidades de comunicação").obrigatorio
    assert _requisito(vaga, "Perfil analítico").obrigatorio
    assert not _requisito(vaga, "Excel").obrigatorio


def test_linha_com_desejavel_dentro_de_requisitos():
    vaga = analisar_vaga("Vaga: Dev\nRequisitos:\n- Python\n- Docker (desejável)\n- Inglês avançado será um diferencial")
    assert vaga.competencias["Python"].obrigatoria
    assert not vaga.competencias["Docker"].obrigatoria
    assert vaga.idiomas["Inglês"] == (3, False)
