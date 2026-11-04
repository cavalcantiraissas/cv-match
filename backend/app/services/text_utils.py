"""Normalização de texto, busca de termos e remoção de dados pessoais."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache


def sem_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in decomposto if not unicodedata.combining(ch))


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e com espaços simples. Mantém + # . / para termos como C++."""
    texto = sem_acentos(texto).lower()
    texto = texto.replace(" ", " ")
    return re.sub(r"\s+", " ", texto).strip()


@lru_cache(maxsize=4096)
def padrao_termo(termo: str, sensivel: bool) -> re.Pattern[str]:
    # Fronteira "manual": o termo não pode estar colado a letras/dígitos.
    # \b não funciona para termos que terminam em símbolos (C++, C#, .NET).
    # Espaços do termo aceitam qualquer espaço/quebra de linha do texto.
    corpo = r"\s+".join(re.escape(p) for p in termo.split())
    flags = 0 if sensivel else re.IGNORECASE
    return re.compile(rf"(?<![\w]){corpo}(?![\w+#])", flags)


def _por_caractere(texto: str, minusculas: bool) -> str:
    """Remove acentos caractere a caractere, preservando o comprimento (e as posições)."""
    saida = []
    for ch in texto:
        base = sem_acentos(ch) or " "
        base = base[0]
        saida.append(base.lower() if minusculas else base)
    return "".join(saida)


class TextoBusca:
    """
    Texto preparado para buscar termos do catálogo.

    As versões sem acento têm o mesmo comprimento do original, então a posição
    de um termo encontrado serve para recortar o trecho original (com acentos)
    como evidência.
    """

    def __init__(self, texto: str):
        self.original = texto
        self.minusculo = _por_caractere(texto, minusculas=True)
        self.sem_acento = _por_caractere(texto, minusculas=False)

    def iterar(self, sinonimo: str):
        """Prefixo "=" no sinônimo significa busca sensível a maiúsculas."""
        if sinonimo.startswith("="):
            return padrao_termo(sem_acentos(sinonimo[1:]), True).finditer(self.sem_acento)
        return padrao_termo(sinonimo, False).finditer(self.minusculo)

    def buscar(self, sinonimo: str) -> re.Match[str] | None:
        return next(iter(self.iterar(sinonimo)), None)

    def contem(self, padrao: str) -> re.Match[str] | None:
        return re.search(padrao, self.minusculo)

    def trecho(self, m: re.Match[str], margem: int = 70) -> str:
        return trecho(self.original, m.start(), m.end(), margem)

    def termo_original(self, m: re.Match[str]) -> str:
        return re.sub(r"\s+", " ", self.original[m.start(): m.end()])


def encontrar_termo(sinonimo: str, texto: str) -> re.Match[str] | None:
    return TextoBusca(texto).buscar(sinonimo)


def dividir_frases(texto: str, minimo: int = 25) -> list[str]:
    """Divide em frases/itens curtos, úteis como unidades de evidência."""
    partes: list[str] = []
    for linha in texto.splitlines():
        linha = linha.strip(" \t•·▪●◦-–—*")
        if not linha:
            continue
        for frase in re.split(r"(?<=[.;!?])\s+", linha):
            frase = frase.strip()
            if len(frase) >= minimo:
                partes.append(frase)
    return partes


def trecho(texto: str, inicio: int, fim: int, margem: int = 70) -> str:
    """Recorta um trecho legível ao redor de uma posição, sem passar da linha do termo."""
    linha_ini = texto.rfind("\n", 0, inicio) + 1
    linha_fim = texto.find("\n", fim)
    linha_fim = len(texto) if linha_fim == -1 else linha_fim
    a = max(linha_ini, inicio - margem)
    b = min(linha_fim, fim + margem)
    if a > linha_ini:
        espaco = texto.find(" ", a, inicio)
        a = espaco + 1 if espaco != -1 else a
    if b < linha_fim:
        espaco = texto.rfind(" ", fim, b)
        b = espaco if espaco != -1 else b
    resultado = re.sub(r"\s+", " ", texto[a:b]).strip(" •·▪●-–—*")
    return ("…" if a > linha_ini else "") + resultado + ("…" if b < linha_fim else "")


# --- Privacidade -------------------------------------------------------------

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_TELEFONE = re.compile(r"(?<!\d)(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[-\s.]?\d{4}(?!\d)")
_CPF = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
_CEP = re.compile(r"(?<!\d)\d{5}-\d{3}(?!\d)")
# Linhas curtas do tipo "Rótulo: valor" com características pessoais.
_ROTULO_PESSOAL = re.compile(
    r"^\s*(data de nascimento|nascimento|idade|estado civil|sexo|genero|nacionalidade|naturalidade|"
    r"endereco|rg|cpf|cnh|filhos|religiao|date of birth|age|marital status|gender|address)\s*[:\-]",
)
_IDADE = re.compile(r"\b\d{2} anos\b(?! de experiencia)|\bnascid[oa] em\b|\b(solteir|casad|divorciad|viuv)[oa]\b")


def remover_dados_pessoais(texto: str) -> str:
    """
    Remove dados de contato e características pessoais do texto.

    Eles não são usados na análise (que considera apenas critérios
    profissionais), não precisam ser armazenados e nunca são enviados à IA.
    """
    texto = _EMAIL.sub("[e-mail removido]", texto)
    texto = _CPF.sub("[documento removido]", texto)
    texto = _CEP.sub("[CEP removido]", texto)
    texto = _TELEFONE.sub(_substituir_telefone, texto)

    linhas = []
    for linha in texto.splitlines():
        norm = normalizar(linha)
        if _ROTULO_PESSOAL.match(norm) or (len(norm) < 60 and _IDADE.search(norm) and "experiencia" not in norm):
            linhas.append("[informação pessoal removida]")
        else:
            linhas.append(linha)
    return "\n".join(linhas)


def _substituir_telefone(m: re.Match[str]) -> str:
    digitos = re.sub(r"\D", "", m.group(0))
    # Evita apagar intervalos de anos como "2019 2021" ou números curtos.
    if len(digitos) < 10 or re.fullmatch(r"(19|20)\d{2}(19|20)\d{2}", digitos):
        return m.group(0)
    return "[telefone removido]"
