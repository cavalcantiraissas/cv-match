"""
Leitura estruturada da descrição da vaga.

Regras para obrigatório x desejável (em ordem de prioridade):
1. Palavras na própria linha: "desejável", "diferencial", "nice to have", "plus"
   tornam o item desejável; "obrigatório", "imprescindível", "essencial" o tornam obrigatório.
2. A seção em que a linha está: "Requisitos/Qualificações" -> obrigatório;
   "Diferenciais/Desejável" -> desejável.
3. Tecnologias citadas só em "Responsabilidades/Atividades" entram como desejáveis:
   a vaga as menciona, mas não as exige explicitamente.
4. Vagas sem seções: linhas com cara de requisito (competência, anos, formação,
   idioma, "experiência com...") são tratadas como obrigatórias.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.catalogo import (
    AREAS_FORMACAO,
    CERTIFICACOES,
    COMPETENCIA_POR_NOME,
    COMPETENCIAS,
    IDIOMAS,
    NIVEIS_FORMACAO,
    NIVEIS_IDIOMA,
    NIVEIS_SENIORIDADE,
)
from app.services.text_utils import TextoBusca, normalizar

_CUE_DESEJAVEL = re.compile(
    r"desejave|diferencia|nice to have|nice-to-have|\bplus\b|\bbonus\b|preferencia|preferencialmente|"
    r"sera um|e um plus|seria otimo|good to have|is a plus|would be great|\bideal\b"
)
_CUE_OBRIGATORIO = re.compile(r"obrigatori|imprescindive|indispensave|essencia|mandatory|required|\bmust\b|necessario")
_CUE_REQUISITO = re.compile(
    r"experiencia|conhecimento|dominio|vivencia|familiaridade|habilidade|capacidade|formacao|graduac|"
    r"superior|ingles|espanhol|certificac|experience|knowledge|proficien|saber|atuacao"
)

# tipo de seção -> palavras que identificam o título
_TITULOS_VAGA: list[tuple[str, tuple[str, ...]]] = [
    ("diferenciais", ("desejave", "diferencia", "nice to have", "plus", "bonus", "preferencia", "seria otimo")),
    ("requisitos", (
        "requisito", "qualificac", "o que esperamos", "o que buscamos", "o que procuramos", "precisa ter",
        "voce precisa", "must have", "requirements", "qualifications", "pre-requisito", "perfil", "competencias",
        "conhecimentos", "habilidades", "obrigatori", "skills", "o que voce precisa", "what you need",
        "what we're looking for", "what we are looking for",
    )),
    ("responsabilidades", (
        "responsabilidade", "atividade", "atribuic", "o que voce vai fazer", "o que voce ira fazer", "o que vai fazer",
        "dia a dia", "responsibilities", "what you'll do", "what you will do", "desafios", "suas missoes",
    )),
    ("beneficios", ("beneficio", "oferecemos", "benefits", "remunerac", "salario", "perks")),
    ("sobre", ("sobre", "quem somos", "about", "a empresa", "nossa empresa", "nosso time", "a vaga")),
    ("info", ("local", "modelo de trabalho", "regime", "contratacao", "jornada", "horario", "localizacao")),
]

_ANOS = re.compile(r"(\d{1,2})\s*\+?\s*(?:(?:a|-|ou mais|or more)\s*\d{0,2}\s*)?(?:anos?|years?)")
_AFINS = re.compile(r"afins|correlat|relacionad|similar|areas de tecnologia|areas de exatas|ou equivalente|related field")
_ACEITA_CURSANDO = re.compile(r"cursando|em andamento|ou cursando|ultimos (anos|semestres)")
_SIGLAS_IGNORADAS = {
    "PJ", "CLT", "PCD", "RH", "TI", "CNPJ", "VR", "VA", "PLR", "US", "EUA", "BR", "SP", "RJ", "MG", "OU", "E", "HR",
    "OK", "CEO", "CTO", "SA", "LTDA", "ME", "API", "APIS",
}


@dataclass
class RequisitoVaga:
    texto: str
    obrigatorio: bool
    origem: str  # requisitos | diferenciais | geral
    tipo: str  # competencia | comportamental | experiencia | formacao | idioma | certificacao | outro
    competencias: list[str] = field(default_factory=list)
    alternativas: bool = False  # "React ou Vue": basta uma
    anos: int | None = None
    idioma: tuple[str, int | None] | None = None
    formacao: dict | None = None
    certificacoes: list[str] = field(default_factory=list)


@dataclass
class CompetenciaVaga:
    nome: str
    tipo: str
    obrigatoria: bool
    termo: str  # como aparece na vaga (usado na checagem literal de ATS)
    origem: str


@dataclass
class PalavraChaveVaga:
    nome: str  # nome canônico (ou a sigla, se não estiver no catálogo)
    termo: str  # forma exata usada na vaga
    obrigatoria: bool
    no_catalogo: bool


@dataclass
class VagaAnalisada:
    texto: str
    cargo: str
    nivel: str | None
    anos_tipicos_nivel: int | None
    requisitos: list[RequisitoVaga]
    competencias: dict[str, CompetenciaVaga]
    responsabilidades: list[str]
    anos_experiencia: int | None
    formacao: dict | None
    idiomas: dict[str, tuple[int | None, bool]]
    certificacoes: dict[str, bool]
    palavras_chave: list[PalavraChaveVaga]
    estruturada: bool


def _tipo_titulo(linha: str) -> str | None:
    if re.match(r"^\s*[•·▪●\-–—*]", linha):  # itens de lista nunca são títulos
        return None
    bruto = linha.strip().strip("#|").strip()
    if not bruto or len(bruto) > 70 or len(bruto.split()) > 9:
        return None
    norm = normalizar(bruto)
    com_dois_pontos = ":" in norm
    if re.search(r"[.;]$", norm):
        return None
    if not com_dois_pontos:
        # Sem ":" só aceitamos títulos curtos que não citem competências
        # (evita tratar "Habilidades de comunicação" como título).
        if len(norm.split()) > 4 or _competencias_na_linha(bruto):
            return None
    norm = norm.split(":")[0]
    for tipo, palavras in _TITULOS_VAGA:
        if any(p in norm for p in palavras):
            # Linhas como "Inglês avançado é um diferencial" não são títulos.
            return tipo
    return None


def _extrair_cargo(linhas: list[str]) -> tuple[str, int | None]:
    """Devolve o cargo e o índice da linha de onde ele veio."""
    for i, linha in enumerate(linhas[:8]):
        m = re.match(r"^\s*(vaga|cargo|titulo|título|posicao|posição|position|job title|role)\s*[:\-]\s*(.+)$", linha, re.I)
        if m:
            return m.group(2).strip()[:120], i
    for i, linha in enumerate(linhas[:5]):
        limpa = linha.strip().strip("#*").strip()
        if limpa and len(limpa.split()) <= 10 and not _tipo_titulo(limpa) and not limpa.endswith("."):
            return limpa[:120], i
    return "Vaga sem título identificado", None


def _extrair_nivel(cargo: str, texto: str) -> tuple[str | None, int | None]:
    for fonte in (normalizar(cargo), normalizar(texto[:600])):
        for padrao, rotulo, anos in NIVEIS_SENIORIDADE:
            if re.search(padrao, fonte):
                return rotulo, anos
    return None, None


def _competencias_na_linha(linha: str) -> list[tuple[str, str]]:
    """Competências do catálogo citadas na linha, com o termo exato usado."""
    busca = TextoBusca(linha)
    achadas: list[tuple[str, str]] = []
    for comp in COMPETENCIAS:
        for s in comp.sinonimos:
            m = busca.buscar(s)
            if m:
                achadas.append((comp.nome, busca.termo_original(m)))
                break
    # Remove competências cujo termo está contido no de outra mais específica
    # (ex.: "React Native" também casa "React").
    return [(n, t) for n, t in achadas if not any(
        outro != n and t.lower() in termo.lower() and len(termo) > len(t) for outro, termo in achadas
    )]


def _classificar_linha(linha: str, obrigatorio: bool, origem: str) -> RequisitoVaga:
    norm = normalizar(linha)
    req = RequisitoVaga(texto=linha.strip(" \t•·▪●-–—*"), obrigatorio=obrigatorio, origem=origem, tipo="outro")

    comps = _competencias_na_linha(linha)
    req.competencias = [n for n, _ in comps]
    req.alternativas = len(comps) > 1 and bool(re.search(r"\bou\b|\bor\b", norm))

    for nome, sinonimos in IDIOMAS.items():
        if any(re.search(rf"\b{s}\b", norm) for s in sinonimos):
            nivel = next((v for p, v, _ in NIVEIS_IDIOMA if re.search(p, norm)), None)
            req.idioma = (nome, nivel)
            break

    for padrao, nivel, rotulo in sorted(NIVEIS_FORMACAO, key=lambda x: x[1]):
        if re.search(padrao, norm) and re.search(r"formac|graduac|superior|bacharel|curso|mestrad|doutorad|pos|tecnico|degree|ensino", norm):
            busca = TextoBusca(linha)
            areas = [a for a, (_, sins) in AREAS_FORMACAO.items() if any(busca.buscar(s) for s in sins)]
            req.formacao = {
                "nivel": nivel, "rotulo": rotulo, "areas": areas,
                "afins": bool(_AFINS.search(norm)), "aceita_cursando": bool(_ACEITA_CURSANDO.search(norm)),
            }
            break

    req.certificacoes = [n for n, padroes in CERTIFICACOES.items() if any(re.search(p, norm) for p in padroes)]
    if "experien" in norm or "atuacao" in norm or "years" in norm:
        m = _ANOS.search(norm)
        if m and 0 < int(m.group(1)) <= 30:
            req.anos = int(m.group(1))

    if req.idioma:
        req.tipo = "idioma"
    elif req.formacao:
        req.tipo = "formacao"
    elif req.certificacoes or "certificac" in norm:
        req.tipo = "certificacao"
    elif req.anos is not None:
        req.tipo = "experiencia"
    elif comps and all(COMPETENCIA_POR_NOME[n].tipo == "comportamental" for n in req.competencias):
        req.tipo = "comportamental"
    elif comps:
        req.tipo = "competencia"
    return req


def analisar_vaga(texto: str) -> VagaAnalisada:
    linhas = [l for l in texto.splitlines() if l.strip()]
    cargo, linha_cargo = _extrair_cargo(linhas)
    nivel, anos_nivel = _extrair_nivel(cargo, texto)

    secao_atual = "geral"
    estruturada = False
    requisitos: list[RequisitoVaga] = []
    responsabilidades: list[str] = []
    competencias: dict[str, CompetenciaVaga] = {}
    siglas: dict[str, bool] = {}

    def registrar(nome: str, termo: str, obrigatoria: bool, origem: str):
        atual = competencias.get(nome)
        if atual is None:
            competencias[nome] = CompetenciaVaga(nome, COMPETENCIA_POR_NOME[nome].tipo, obrigatoria, termo, origem)
        elif obrigatoria and not atual.obrigatoria:
            atual.obrigatoria, atual.termo, atual.origem = True, termo, origem

    for indice, linha in enumerate(linhas):
        if indice == linha_cargo:
            continue
        tipo_titulo = _tipo_titulo(linha)
        if tipo_titulo:
            secao_atual = tipo_titulo
            estruturada = estruturada or tipo_titulo in ("requisitos", "diferenciais", "responsabilidades")
            # Títulos como "Requisitos: Python e SQL" trazem conteúdo na mesma linha.
            _, _, resto = linha.partition(":")
            if not resto.strip():
                continue
            linha = resto
        if secao_atual in ("beneficios", "sobre", "info"):
            continue

        norm = normalizar(linha)
        comps_linha = _competencias_na_linha(linha)
        if secao_atual == "responsabilidades":
            responsabilidades.append(linha.strip(" \t•·▪●-–—*"))
            for nome, termo in comps_linha:
                registrar(nome, termo, False, "responsabilidades")
            continue

        if secao_atual == "diferenciais":
            obrigatorio = bool(_CUE_OBRIGATORIO.search(norm)) and not _CUE_DESEJAVEL.search(norm)
        else:
            obrigatorio = not _CUE_DESEJAVEL.search(norm)
        req = _classificar_linha(linha, obrigatorio, secao_atual)

        if secao_atual == "geral" and req.tipo == "outro" and not _CUE_REQUISITO.search(norm):
            # Texto institucional em vagas sem seções: não é requisito nem atividade.
            continue
        if len(req.texto) < 3:
            continue
        requisitos.append(req)
        for nome, termo in comps_linha:
            registrar(nome, termo, req.obrigatorio, secao_atual)
        for sigla in re.findall(r"\b[A-Z]{2,6}\b", linha):
            if sigla not in _SIGLAS_IGNORADAS and not any(
                normalizar(sigla) in [s.lstrip("=").lower() for s in COMPETENCIA_POR_NOME[n].sinonimos] for n in competencias
            ):
                siglas[sigla] = siglas.get(sigla, False) or req.obrigatorio

    anos_obrig = [r.anos for r in requisitos if r.anos and r.obrigatorio]
    formacoes = [r for r in requisitos if r.formacao]
    formacao = None
    if formacoes:
        principal = next((r for r in formacoes if r.obrigatorio), formacoes[0])
        formacao = {**principal.formacao, "obrigatorio": principal.obrigatorio}

    idiomas: dict[str, tuple[int | None, bool]] = {}
    for r in requisitos:
        if r.idioma and r.idioma[0] != "Português":
            idiomas[r.idioma[0]] = (r.idioma[1], r.obrigatorio or idiomas.get(r.idioma[0], (None, False))[1])

    certificacoes: dict[str, bool] = {}
    for r in requisitos:
        for c in r.certificacoes:
            certificacoes[c] = certificacoes.get(c, False) or r.obrigatorio

    palavras = [
        PalavraChaveVaga(c.nome, c.termo, c.obrigatoria, True)
        for c in competencias.values() if c.tipo != "comportamental"
    ]
    palavras += [PalavraChaveVaga(s, s, o, False) for s, o in list(siglas.items())[:8]]

    return VagaAnalisada(
        texto=texto,
        cargo=cargo,
        nivel=nivel,
        anos_tipicos_nivel=anos_nivel,
        requisitos=requisitos,
        competencias=competencias,
        responsabilidades=responsabilidades,
        anos_experiencia=max(anos_obrig) if anos_obrig else None,
        formacao=formacao,
        idiomas=idiomas,
        certificacoes=certificacoes,
        palavras_chave=palavras,
        estruturada=estruturada,
    )
