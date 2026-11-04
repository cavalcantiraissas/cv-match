"""
Leitura estruturada do currículo.

Identifica seções pelos títulos, as competências do catálogo (com a força da
evidência: usada em experiência/projeto ou apenas listada), o tempo de
experiência a partir dos períodos informados, a formação, idiomas e certificações.

Dados de contato e características pessoais (idade, gênero, endereço, foto etc.)
não são usados aqui: o texto chega já sem eles (ver text_utils.remover_dados_pessoais)
e a seção de informações pessoais é ignorada na análise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from app.core.catalogo import (
    AREAS_FORMACAO,
    CERTIFICACOES,
    COMPETENCIA_POR_NOME,
    COMPETENCIAS,
    IDIOMAS,
    NIVEIS_FORMACAO,
    NIVEIS_IDIOMA,
)
from app.services.text_utils import TextoBusca, dividir_frases, normalizar

# chave -> (rótulo, títulos possíveis já normalizados)
SECOES: dict[str, tuple[str, tuple[str, ...]]] = {
    "resumo": ("Resumo profissional", (
        "resumo", "resumo profissional", "perfil", "perfil profissional", "sobre mim", "sobre", "objetivo",
        "objetivo profissional", "summary", "professional summary", "profile", "about me", "objective", "apresentacao",
    )),
    "experiencia": ("Experiência profissional", (
        "experiencia", "experiencias", "experiencia profissional", "experiencias profissionais",
        "historico profissional", "trajetoria profissional", "experience", "work experience",
        "professional experience", "employment history", "atuacao profissional",
    )),
    "formacao": ("Formação acadêmica", (
        "formacao", "formacao academica", "educacao", "escolaridade", "education", "academic background",
        "formacao academica e complementar",
    )),
    "competencias": ("Competências técnicas", (
        "competencias", "competencias tecnicas", "habilidades", "habilidades tecnicas", "conhecimentos",
        "conhecimentos tecnicos", "skills", "technical skills", "hard skills", "soft skills", "tecnologias",
        "stack", "ferramentas", "competencias e habilidades", "habilidades e competencias", "core competencies",
        "competencias comportamentais",
    )),
    "idiomas": ("Idiomas", ("idiomas", "idioma", "languages", "linguas")),
    "certificacoes": ("Certificações e cursos", (
        "certificacoes", "certificados", "certificacoes e cursos", "cursos e certificacoes", "cursos",
        "cursos complementares", "formacao complementar", "certifications", "courses", "licenses & certifications",
        "licencas e certificados",
    )),
    "projetos": ("Projetos", ("projetos", "projetos pessoais", "projetos relevantes", "projects", "portfolio", "portifolio")),
    "outros": ("Outras informações", (
        "voluntariado", "trabalho voluntario", "premios", "premiacoes", "publicacoes", "atividades extracurriculares",
        "awards", "volunteering", "publications", "informacoes adicionais", "additional information",
    )),
    "informacoes": ("Informações pessoais e contato", (
        "contato", "contatos", "dados pessoais", "informacoes pessoais", "contact", "personal information",
    )),
}
ROTULO_SECAO = {chave: rotulo for chave, (rotulo, _) in SECOES.items()}
_TITULO_PARA_SECAO = {titulo: chave for chave, (_, titulos) in SECOES.items() for titulo in titulos}

# Seções em que a menção a uma competência indica uso prático.
SECOES_PRATICA = {"experiencia", "projetos", "certificacoes", "outros"}
SECOES_IGNORADAS = {"informacoes"}


@dataclass
class Secao:
    chave: str
    rotulo: str
    texto: str


@dataclass
class EvidenciaCompetencia:
    nome: str
    nivel: str  # "forte" | "listada"
    secao: str
    trecho: str
    ocorrencias: int = 1
    inferida_de: str | None = None


@dataclass
class Formacao:
    nivel: int = 0
    rotulo: str = "Não identificada"
    em_andamento: bool = False
    nivel_concluido: int = 0
    areas: list[str] = field(default_factory=list)
    trecho: str = ""


@dataclass
class Idioma:
    nome: str
    nivel: int | None
    rotulo: str
    trecho: str


@dataclass
class CurriculoAnalisado:
    texto: str
    secoes: list[Secao]
    competencias: dict[str, EvidenciaCompetencia]
    anos_experiencia: float | None
    anos_declarados: float | None
    periodos: list[tuple[date, date]]
    formacao: Formacao
    idiomas: dict[str, Idioma]
    certificacoes: dict[str, str]  # nome -> trecho
    frases: list[tuple[str, str]]  # (chave da seção, frase) usadas como evidência semântica

    def secao(self, chave: str) -> str:
        return "\n".join(s.texto for s in self.secoes if s.chave == chave)

    def texto_profissional(self) -> str:
        return "\n".join(s.texto for s in self.secoes if s.chave not in SECOES_IGNORADAS)


# --- Seções -------------------------------------------------------------------

def _titulo_de_secao(linha: str) -> tuple[str, str] | None:
    """Se a linha for um título de seção, devolve (chave, conteúdo após ':')."""
    bruto = linha.strip().strip("•·▪●-–—*#|").strip()
    if not bruto or len(bruto) > 60:
        return None
    titulo, _, resto = bruto.partition(":")
    norm = normalizar(titulo).rstrip(".").strip()
    norm = re.sub(r"[^a-z& ]", "", norm).strip()
    if norm in _TITULO_PARA_SECAO:
        return _TITULO_PARA_SECAO[norm], resto.strip()
    return None


def identificar_secoes(texto: str) -> list[Secao]:
    blocos: list[tuple[str, list[str]]] = [("informacoes", [])]
    for linha in texto.splitlines():
        achado = _titulo_de_secao(linha)
        if achado:
            chave, resto = achado
            blocos.append((chave, [resto] if resto else []))
        else:
            blocos[-1][1].append(linha)

    # Agrupa seções repetidas (ex.: "Hard skills" e "Soft skills") mantendo a ordem.
    agrupado: dict[str, list[str]] = {}
    for chave, linhas in blocos:
        conteudo = "\n".join(linhas).strip()
        if conteudo:
            agrupado.setdefault(chave, []).append(conteudo)
    secoes = [Secao(chave, ROTULO_SECAO[chave], "\n\n".join(partes)) for chave, partes in agrupado.items()]

    # Sem nenhum título reconhecido, o conteúdo todo vira "geral" para não ser ignorado.
    if len(secoes) == 1 and secoes[0].chave == "informacoes":
        secoes = [Secao("geral", "Conteúdo do currículo", secoes[0].texto)]
    return secoes


# --- Competências ---------------------------------------------------------------

def detectar_competencias(secoes: list[Secao]) -> dict[str, EvidenciaCompetencia]:
    encontradas: dict[str, EvidenciaCompetencia] = {}
    sem_titulos = len(secoes) == 1 and secoes[0].chave == "geral"
    for secao in secoes:
        if secao.chave in SECOES_IGNORADAS:
            continue
        busca = TextoBusca(secao.texto)
        for comp in COMPETENCIAS:
            ocorrencias, primeira = 0, None
            for sinonimo in comp.sinonimos:
                for m in busca.iterar(sinonimo):
                    ocorrencias += 1
                    primeira = primeira or m
            if not ocorrencias:
                continue
            nivel = "forte" if secao.chave in SECOES_PRATICA else "listada"
            nova = EvidenciaCompetencia(comp.nome, nivel, secao.chave, busca.trecho(primeira), ocorrencias)
            atual = encontradas.get(comp.nome)
            if atual is None:
                encontradas[comp.nome] = nova
            else:
                atual.ocorrencias += ocorrencias
                if atual.nivel != "forte" and nivel == "forte":
                    atual.nivel, atual.secao, atual.trecho = "forte", nova.secao, nova.trecho

    if sem_titulos:
        # Sem seções não dá para saber onde a competência foi usada; repetição é o melhor sinal.
        for ev in encontradas.values():
            ev.nivel = "forte" if ev.ocorrencias >= 2 else "listada"

    # Competências comprovadas por outras (ex.: PostgreSQL comprova SQL).
    for nome, ev in list(encontradas.items()):
        for implicada in COMPETENCIA_POR_NOME[nome].implica:
            atual = encontradas.get(implicada)
            if atual is None or (atual.nivel == "listada" and ev.nivel == "forte"):
                encontradas[implicada] = EvidenciaCompetencia(
                    implicada, ev.nivel, ev.secao, ev.trecho, 0, inferida_de=nome
                )
    return encontradas


# --- Experiência ------------------------------------------------------------------

_MES = r"(?:jan|fev|feb|mar|abr|apr|mai|may|jun|jul|ago|aug|set|sep|out|oct|nov|dez|dec)[a-z]*\.?"
_DATA = rf"(?:{_MES}\s*(?:de\s+)?[/\-.]?\s*|\d{{1,2}}\s*[/.\-]\s*)?(?:19|20)\d{{2}}"
_FIM_ATUAL = r"atual(?:mente)?|presente|o momento|momento|hoje|present|current|now|em andamento"
PADRAO_PERIODO = re.compile(
    rf"(?P<ini>{_DATA})\s*(?:[-–—·]+|\s(?:a|ate|to|until)\s)\s*(?P<fim>{_DATA}|{_FIM_ATUAL})"
)
_MESES = {
    "jan": 1, "fev": 2, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "mai": 5, "may": 5, "jun": 6, "jul": 7,
    "ago": 8, "aug": 8, "set": 9, "sep": 9, "out": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}
_ANOS_DECLARADOS = re.compile(r"(\d{1,2})\+?\s*anos de (?:experiencia|atuacao)|(\d{1,2})\+?\s*years of experience")


def _ler_data(texto: str, hoje: date, inicio: bool) -> date | None:
    if re.fullmatch(_FIM_ATUAL, texto.strip()):
        return hoje
    ano = int(re.findall(r"(?:19|20)\d{2}", texto)[-1])
    mes = 1 if inicio else 12
    nome_mes = re.match(r"([a-z]{3})", texto.strip())
    numero = re.match(r"(\d{1,2})\s*[/.\-]", texto.strip())
    if nome_mes and nome_mes.group(1) in _MESES:
        mes = _MESES[nome_mes.group(1)]
    elif numero and 1 <= int(numero.group(1)) <= 12:
        mes = int(numero.group(1))
    return date(ano, mes, 1)


def calcular_experiencia(texto: str, hoje: date) -> tuple[float | None, list[tuple[date, date]]]:
    """Soma os períodos encontrados, sem contar duas vezes os que se sobrepõem."""
    periodos: list[tuple[date, date]] = []
    for m in PADRAO_PERIODO.finditer(normalizar(texto)):
        ini = _ler_data(m.group("ini"), hoje, inicio=True)
        fim = _ler_data(m.group("fim"), hoje, inicio=False)
        if ini and fim and ini <= fim <= hoje and (fim.year - ini.year) <= 50:
            periodos.append((ini, fim))
    if not periodos:
        return None, []
    periodos.sort()
    meses, (atual_ini, atual_fim) = 0, periodos[0]
    for ini, fim in periodos[1:]:
        if ini <= atual_fim:
            atual_fim = max(atual_fim, fim)
        else:
            meses += _meses_entre(atual_ini, atual_fim)
            atual_ini, atual_fim = ini, fim
    meses += _meses_entre(atual_ini, atual_fim)
    return round(meses / 12, 1), periodos


def _meses_entre(ini: date, fim: date) -> int:
    return (fim.year - ini.year) * 12 + (fim.month - ini.month) + 1


# --- Formação, idiomas e certificações ---------------------------------------------

_EM_ANDAMENTO = re.compile(r"cursando|em andamento|em curso|previsao de conclusao|conclusao prevista|incomplet|trancad|in progress|expected|ongoing|\(atual\)")


def detectar_formacao(texto: str) -> Formacao:
    formacao = Formacao()
    originais = [l.strip() for l in texto.splitlines() if l.strip()]
    linhas = [normalizar(l) for l in originais]
    for i, linha in enumerate(linhas):
        contexto = " ".join(linhas[i: i + 2])
        for padrao, nivel, rotulo in NIVEIS_FORMACAO:
            if re.search(padrao, linha):
                andamento = bool(_EM_ANDAMENTO.search(contexto)) or bool(re.search(rf"{_DATA}\s*[-–—]\s*(?:{_FIM_ATUAL})", contexto))
                if not andamento:
                    formacao.nivel_concluido = max(formacao.nivel_concluido, nivel)
                if nivel > formacao.nivel or (nivel == formacao.nivel and formacao.em_andamento and not andamento):
                    formacao.nivel, formacao.rotulo, formacao.em_andamento = nivel, rotulo, andamento
                    formacao.trecho = " ".join(originais[i: i + 2])[:200]
                break
    busca = TextoBusca(texto)
    for area, (_, sinonimos) in AREAS_FORMACAO.items():
        if any(busca.buscar(s) for s in sinonimos):
            formacao.areas.append(area)
    return formacao


def detectar_idiomas(texto: str) -> dict[str, Idioma]:
    encontrados: dict[str, Idioma] = {}
    busca = TextoBusca(texto)
    todos = "|".join(x for v in IDIOMAS.values() for x in v)
    for nome, sinonimos in IDIOMAS.items():
        for s in sinonimos:
            m = busca.buscar(s)
            if not m:
                continue
            # O nível costuma vir logo depois do idioma, na mesma linha ("Inglês - avançado").
            janela = busca.minusculo[m.end(): m.end() + 45].split("\n")[0]
            janela = re.split(rf"\b(?:{todos})\b", janela)[0]
            nivel, rotulo = None, "Nível não informado"
            for padrao, valor, rot in NIVEIS_IDIOMA:
                if re.search(padrao, janela):
                    nivel, rotulo = valor, rot
                    break
            encontrados[nome] = Idioma(nome, nivel, rotulo, busca.trecho(m, 30))
            break
    return encontrados


def detectar_certificacoes(texto: str) -> dict[str, str]:
    busca = TextoBusca(texto)
    achadas: dict[str, str] = {}
    for nome, padroes in CERTIFICACOES.items():
        for p in padroes:
            m = busca.contem(p)
            if m:
                achadas[nome] = busca.trecho(m, 50)
                break
    return achadas


# --- Ponto de entrada ------------------------------------------------------------

def analisar_curriculo(texto: str, hoje: date | None = None) -> CurriculoAnalisado:
    hoje = hoje or date.today()
    secoes = identificar_secoes(texto)
    por_chave = {s.chave: s.texto for s in secoes}
    profissional = "\n".join(s.texto for s in secoes if s.chave not in SECOES_IGNORADAS)

    base_experiencia = por_chave.get("experiencia") or "\n".join(
        s.texto for s in secoes if s.chave not in SECOES_IGNORADAS | {"formacao", "certificacoes"}
    )
    anos, periodos = calcular_experiencia(base_experiencia, hoje)
    declarados = [int(a or b) for a, b in _ANOS_DECLARADOS.findall(normalizar(profissional))]

    frases = [
        (s.chave, f)
        for s in secoes
        if s.chave not in SECOES_IGNORADAS
        for f in dividir_frases(s.texto)
    ]
    return CurriculoAnalisado(
        texto=texto,
        secoes=secoes,
        competencias=detectar_competencias(secoes),
        anos_experiencia=anos,
        anos_declarados=float(max(declarados)) if declarados else None,
        periodos=periodos,
        formacao=detectar_formacao(por_chave.get("formacao") or profissional),
        idiomas=detectar_idiomas(por_chave.get("idiomas") or profissional),
        certificacoes=detectar_certificacoes(profissional),
        frases=frases,
    )
