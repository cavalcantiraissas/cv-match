import pymupdf
import pytest

from app.services.pdf_parser import ErroPDF, extrair_texto_pdf
from tests.fixtures import CURRICULO_DEV_PYTHON, gerar_pdf, gerar_pdf_sem_texto

LIMITE = 5 * 1024 * 1024


def _codigo(conteudo: bytes, max_bytes: int = LIMITE, max_paginas: int = 10) -> str:
    with pytest.raises(ErroPDF) as erro:
        extrair_texto_pdf(conteudo, max_bytes, max_paginas)
    return erro.value.codigo


def test_extrai_texto_de_pdf_valido():
    pdf = extrair_texto_pdf(gerar_pdf(CURRICULO_DEV_PYTHON), LIMITE, 10)
    assert pdf.paginas == 1
    assert "FastAPI e PostgreSQL" in pdf.texto
    assert "EXPERIÊNCIA PROFISSIONAL" in pdf.texto  # acentos preservados


def test_rejeita_arquivo_vazio():
    assert _codigo(b"") == "arquivo_vazio"


def test_rejeita_arquivo_que_nao_e_pdf():
    assert _codigo(b"isto nao e um pdf, mesmo com a extensao certa") == "formato_invalido"


def test_rejeita_pdf_corrompido():
    assert _codigo(b"%PDF-1.7\n conteudo quebrado sem estrutura") == "pdf_corrompido"


def test_rejeita_arquivo_maior_que_o_limite():
    assert _codigo(gerar_pdf(CURRICULO_DEV_PYTHON), max_bytes=100) == "arquivo_grande"


def test_identifica_pdf_digitalizado_sem_texto():
    assert _codigo(gerar_pdf_sem_texto()) == "pdf_sem_texto"


def test_rejeita_pdf_com_muitas_paginas():
    assert _codigo(gerar_pdf(CURRICULO_DEV_PYTHON * 6), max_paginas=2) == "pdf_muitas_paginas"


def test_rejeita_pdf_protegido_por_senha():
    documento = pymupdf.open()
    documento.new_page().insert_text((50, 50), "Currículo protegido " * 20)
    conteudo = documento.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="segredo", owner_pw="dono")
    assert _codigo(conteudo) == "pdf_protegido"
