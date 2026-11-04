"""
Validação e extração de texto de PDFs com PyMuPDF.

O arquivo é processado apenas em memória: nada é gravado em disco e nenhum
conteúdo do PDF é executado (scripts, anexos e formulários são ignorados;
só a camada de texto é lida).
"""

from __future__ import annotations

from dataclasses import dataclass

import pymupdf as fitz

# Abaixo disso, em média por página, consideramos que o PDF é uma imagem
# digitalizada sem texto selecionável.
MIN_CARACTERES_POR_PAGINA = 80


class ErroPDF(Exception):
    """Erro de validação/leitura com mensagem pronta para o usuário."""

    def __init__(self, mensagem: str, codigo: str):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.codigo = codigo


@dataclass
class PDFExtraido:
    texto: str
    paginas: int


def extrair_texto_pdf(conteudo: bytes, max_bytes: int, max_paginas: int) -> PDFExtraido:
    if not conteudo:
        raise ErroPDF("O arquivo enviado está vazio.", "arquivo_vazio")
    if len(conteudo) > max_bytes:
        raise ErroPDF(
            f"O arquivo tem {len(conteudo) / 1_048_576:.1f} MB. O limite é {max_bytes / 1_048_576:.0f} MB.",
            "arquivo_grande",
        )
    # Verifica a assinatura do arquivo, não só a extensão ou o content-type.
    if not conteudo.lstrip()[:5].startswith(b"%PDF-"):
        raise ErroPDF("O arquivo não é um PDF válido.", "formato_invalido")

    try:
        documento = fitz.open(stream=conteudo, filetype="pdf")
    except Exception:
        raise ErroPDF("Não foi possível abrir o PDF. Ele pode estar corrompido.", "pdf_corrompido")

    with documento:
        if documento.needs_pass:
            raise ErroPDF("O PDF está protegido por senha. Envie uma versão sem senha.", "pdf_protegido")
        if documento.page_count == 0:
            raise ErroPDF("O PDF não tem páginas.", "pdf_vazio")
        if documento.page_count > max_paginas:
            raise ErroPDF(
                f"O PDF tem {documento.page_count} páginas. O limite é {max_paginas} páginas para um currículo.",
                "pdf_muitas_paginas",
            )
        paginas = [pagina.get_text("text", sort=True) for pagina in documento]

    texto = "\n".join(paginas)
    texto = texto.replace("\x00", "").replace("­", "")  # bytes nulos e hifenização suave
    if len(texto.strip()) < MIN_CARACTERES_POR_PAGINA * len(paginas):
        raise ErroPDF(
            "Não encontramos texto selecionável neste PDF. Ele parece ser uma imagem digitalizada "
            "e precisa passar por OCR (reconhecimento de texto) antes da análise. Exporte o currículo "
            "diretamente do editor de texto ou use uma ferramenta de OCR e envie novamente.",
            "pdf_sem_texto",
        )
    return PDFExtraido(texto=texto, paginas=len(paginas))
