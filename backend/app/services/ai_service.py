"""
Camada de IA: sugestões de melhoria e reescrita de seções do currículo.

A IA só interpreta o resultado já calculado pelo motor de compatibilidade; ela
nunca altera o score. Há dois provedores com a mesma interface:

- `ProvedorLocal`: regras determinísticas, funciona sem internet e sem chave.
- `ProvedorGemini`: usa a API do Gemini (camada gratuita) quando GEMINI_API_KEY
  está configurada. Se a chamada falhar, o serviço volta para o provedor local.

Para adicionar outro provedor, implemente `ProvedorIA` e registre em `obter_provedor`.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

from app.core.catalogo import COMPETENCIAS
from app.core.config import Settings, get_settings
from app.schemas.analysis import Sugestao
from app.services.matching_engine import ResultadoMatching
from app.services.resume_analyzer import PADRAO_PERIODO, SECOES_IGNORADAS, CurriculoAnalisado
from app.services.text_utils import TextoBusca, normalizar

logger = logging.getLogger(__name__)

ROTULOS_SECAO_EDITOR = {
    "resumo": "Resumo profissional",
    "experiencia": "Descrição de experiência",
    "projetos": "Descrição de projetos",
    "competencias": "Competências técnicas",
    "formacao": "Formação acadêmica",
    "certificacoes": "Certificações e cursos",
    "geral": "Texto livre",
}


@dataclass
class ContextoVaga:
    """O que a reescrita pode saber sobre a vaga (sem dados pessoais)."""
    cargo: str
    competencias_atendidas: list[str]
    termos_vaga: list[str]


@dataclass
class Reescrita:
    texto: str
    observacoes: list[str]


class ProvedorIA(Protocol):
    nome: str

    def gerar_sugestoes(self, resultado: ResultadoMatching, curriculo: CurriculoAnalisado) -> list[Sugestao]: ...

    def reescrever(self, secao: str, texto: str, vaga: ContextoVaga | None) -> Reescrita: ...


# =====================================================================================
# Provedor local (regras)
# =====================================================================================

_INICIOS_FRACOS = re.compile(
    r"^(eu\s+)?(fui\s+|era\s+|sou\s+)?respons[aá]vel\s+(por|pela|pelo|pelas|pelos)\s+", re.IGNORECASE
)
_PRONOMES = re.compile(r"^(eu|nós|nos)\s+", re.IGNORECASE)
_IRREGULARES = {
    "fazer": "Fiz", "manter": "Mantive", "propor": "Propus", "trazer": "Trouxe", "ter": "Tive", "ser": "Fui",
    "ir": "Fui", "pôr": "Pus", "por": "Pus", "compor": "Compus", "dispor": "Dispus", "obter": "Obtive",
    "conter": "Contive", "reduzir": "Reduzi", "conduzir": "Conduzi", "produzir": "Produzi", "construir": "Construí",
    "distribuir": "Distribuí", "contribuir": "Contribuí", "incluir": "Incluí", "atribuir": "Atribuí",
}
_MARCADORES = re.compile(r"^\s*[•·▪●◦\-–—*]\s*")


def _verbo_no_passado(infinitivo: str) -> str | None:
    """Conjuga um verbo no infinitivo para a 1ª pessoa do pretérito (desenvolver -> Desenvolvi)."""
    v = infinitivo.lower()
    if v in _IRREGULARES:
        return _IRREGULARES[v]
    if v.endswith("car"):
        return (v[:-3] + "quei").capitalize()
    if v.endswith("gar"):
        return (v[:-3] + "guei").capitalize()
    if v.endswith("çar"):
        return (v[:-3] + "cei").capitalize()
    if v.endswith("ar"):
        return (v[:-2] + "ei").capitalize()
    if v.endswith(("er", "ir")):
        return (v[:-2] + "i").capitalize()
    return None


def _reformular_item(item: str) -> tuple[str, bool]:
    """Troca 'Responsável por desenvolver X' por 'Desenvolvi X'. Devolve (texto, mudou)."""
    original = item
    item = _PRONOMES.sub("", item)
    m = _INICIOS_FRACOS.match(item)
    if m:
        resto = item[m.end():]
        primeira, _, depois = resto.partition(" ")
        conjugado = _verbo_no_passado(primeira) if re.fullmatch(r"[a-zà-ú]+(ar|er|ir|or)", primeira.lower()) else None
        if conjugado:
            item = f"{conjugado} {depois}".strip()
        else:
            item = "Responsável " + m.group(3).lower() + " " + resto
    item = item[:1].upper() + item[1:] if item else item
    return item, item != original


def _juntar_linhas_quebradas(texto: str) -> list[str]:
    """Reúne linhas que o PDF quebrou no meio de uma frase, preservando itens de lista."""
    itens: list[str] = []
    for linha in texto.splitlines():
        if not linha.strip():
            if itens and itens[-1] != "":
                itens.append("")
            continue
        novo_item = bool(_MARCADORES.match(linha))
        limpa = _MARCADORES.sub("", linha).strip()
        continua = (
            itens and itens[-1] and not novo_item and not PADRAO_PERIODO.search(normalizar(limpa))
            and not re.search(r"[.:;!?]$", itens[-1]) and (limpa[:1].islower() or limpa[:1].isdigit())
        )
        if continua:
            itens[-1] = f"{itens[-1]} {limpa}"
        else:
            itens.append(("• " if novo_item else "") + limpa)
    while itens and itens[-1] == "":
        itens.pop()
    return itens


def _organizar_competencias(texto: str) -> tuple[str, list[str]]:
    busca = TextoBusca(texto)
    por_grupo: dict[str, list[str]] = {}
    for comp in COMPETENCIAS:
        if any(busca.buscar(s) for s in comp.sinonimos):
            por_grupo.setdefault(comp.grupo, []).append(comp.nome)
    if not por_grupo:
        return texto.strip(), ["Não reconhecemos competências do nosso catálogo neste texto; ele foi mantido como está."]
    linhas = [f"{grupo}: {', '.join(nomes)}" for grupo, nomes in por_grupo.items()]
    # Termos que não estão no catálogo continuam no texto, para nada se perder.
    reconhecidos = {normalizar(s.lstrip("=")) for c in COMPETENCIAS for s in c.sinonimos} | {
        normalizar(n) for nomes in por_grupo.values() for n in nomes
    }
    outros = [
        t.strip() for t in re.split(r"[,;|•\n]", texto)
        if t.strip() and normalizar(t.strip()) not in reconhecidos and len(t.strip()) <= 40
    ]
    if outros:
        linhas.append(f"Outros: {', '.join(dict.fromkeys(outros))}")
    return "\n".join(linhas), [
        "Competências agrupadas por tipo e com a grafia padrão (ex.: “postgres” → “PostgreSQL”).",
        "Confira se cada item corresponde a algo que você realmente usou; remova o que não domina.",
    ]


class ProvedorLocal:
    nome = "local"

    # --- Sugestões ---------------------------------------------------------------

    def gerar_sugestoes(self, resultado: ResultadoMatching, curriculo: CurriculoAnalisado) -> list[Sugestao]:
        s: list[Sugestao] = []
        comps = resultado.competencias
        obrig_ausentes = [c.nome for c in comps if c.obrigatoria and c.evidencia == "ausente" and c.tipo != "comportamental"]
        relacionadas = [c for c in comps if c.obrigatoria and c.evidencia == "relacionada"]
        listadas = [c.nome for c in comps if c.obrigatoria and c.evidencia == "listada"]

        if not curriculo.periodos:
            s.append(Sugestao(
                titulo="Informe os períodos de cada experiência",
                descricao="Use mês e ano de início e fim (ex.: “mar/2021 – atual”). Sem isso, recrutadores e "
                          "sistemas ATS não conseguem calcular seu tempo de experiência.",
                prioridade="alta", secao="experiencia",
            ))
        for c in relacionadas[:3]:
            s.append(Sugestao(
                titulo=f"Deixe explícita sua experiência com {c.nome}",
                descricao=f"{c.justificativa} Se você já trabalhou com {c.nome}, cite em qual experiência ou projeto "
                          "e o que fez. Se não trabalhou, destaque a tecnologia equivalente que conhece.",
                prioridade="alta", secao="experiencia",
            ))
        if listadas:
            s.append(Sugestao(
                titulo="Mostre onde você aplicou as competências listadas",
                descricao=f"{', '.join(listadas[:6])} aparece(m) apenas em listas. Descreva, nas experiências ou "
                          "projetos, uma situação concreta em que você usou cada uma e o resultado obtido.",
                prioridade="alta", secao="experiencia",
            ))
        if obrig_ausentes:
            s.append(Sugestao(
                titulo="Requisitos obrigatórios não encontrados",
                descricao=f"Não encontramos {', '.join(obrig_ausentes[:6])}. Se você tem essa experiência, inclua-a "
                          "com contexto (onde, como e com que resultado). Se não tem, não inclua: considere "
                          "um curso ou projeto prático antes de se candidatar a vagas que exigem esses itens.",
                prioridade="alta", secao="competencias",
            ))

        resumo = curriculo.secao("resumo")
        atendidas = [c.nome for c in comps if c.obrigatoria and c.status == "encontrada"][:5]
        if not resumo:
            s.append(Sugestao(
                titulo="Adicione um resumo profissional",
                descricao="Duas a quatro linhas no topo do currículo, dizendo sua área, seu tempo de experiência e "
                          f"as competências mais fortes que você já tem e a vaga pede ({', '.join(atendidas) or 'as principais'}).",
                prioridade="media", secao="resumo",
            ))
        elif atendidas and sum(1 for n in atendidas if n in curriculo.competencias and TextoBusca(resumo).buscar(n.lower())) < 2:
            s.append(Sugestao(
                titulo="Alinhe o resumo profissional à vaga",
                descricao=f"Seu resumo cita poucas das competências que você comprovou e a vaga pede. Considere mencionar "
                          f"{', '.join(atendidas)} e o cargo de interesse ({resultado.vaga.cargo}).",
                prioridade="media", secao="resumo",
            ))

        experiencia = curriculo.secao("experiencia")
        # Só itens descritivos: linhas com marcador de lista (ou todas, se não houver marcadores),
        # ignorando linhas de cargo/empresa e de período.
        linhas = [l for l in experiencia.splitlines() if len(l.strip()) > 30 and not PADRAO_PERIODO.search(normalizar(l))]
        itens = [l for l in linhas if _MARCADORES.match(l)] or linhas
        sem_numero = [l.strip(" •·▪●-–—*") for l in itens if not re.search(r"\d", l)]
        if itens and len(sem_numero) / len(itens) > 0.6:
            exemplo = sem_numero[0][:110]
            s.append(Sugestao(
                titulo="Adicione resultados mensuráveis",
                descricao=f"A maior parte das descrições não traz números. Ex.: “{exemplo}”. Se você tiver o dado, "
                          "acrescente o impacto (tempo economizado, % de melhoria, volume atendido, tamanho da equipe).",
                prioridade="media", secao="experiencia",
            ))
        if any(_INICIOS_FRACOS.match(_MARCADORES.sub("", l).strip()) for l in experiencia.splitlines()):
            s.append(Sugestao(
                titulo="Comece as descrições com verbos de ação",
                descricao="Troque “Responsável por desenvolver…” por “Desenvolvi…”. Use o editor “Melhorar meu "
                          "currículo” para reescrever a seção de experiência.",
                prioridade="baixa", secao="experiencia",
            ))

        variacoes = [p for p in resultado.palavras_chave if p.status == "variacao"]
        if variacoes:
            s.append(Sugestao(
                titulo="Use os mesmos termos da vaga",
                descricao="Sistemas ATS costumam comparar palavras exatas. A vaga escreve "
                          + ", ".join(f"“{p.termo_na_vaga}”" for p in variacoes[:5])
                          + ", e seu currículo usa outra grafia. Ajuste onde fizer sentido.",
                prioridade="media", secao="competencias",
            ))

        sem_nivel = [i.nome for i in curriculo.idiomas.values() if i.nivel is None and i.nome != "Português"]
        if sem_nivel:
            s.append(Sugestao(
                titulo="Informe o nível dos idiomas",
                descricao=f"{', '.join(sem_nivel)} aparece(m) sem nível. Use básico, intermediário, avançado ou fluente.",
                prioridade="media", secao="idiomas",
            ))

        tecnicas = [c for c in comps if c.tipo in ("tecnica", "ferramenta")]
        if not curriculo.secao("projetos") and len(tecnicas) >= 4:
            s.append(Sugestao(
                titulo="Inclua uma seção de projetos",
                descricao="Projetos (profissionais, acadêmicos ou pessoais) são uma forma direta de comprovar "
                          "tecnologias. Descreva o problema, a solução, as tecnologias usadas e o resultado.",
                prioridade="baixa", secao="projetos",
            ))
        if not s:
            s.append(Sugestao(
                titulo="Currículo bem alinhado",
                descricao="Os principais requisitos estão evidenciados. Revise apenas se as experiências mais "
                          "relevantes para esta vaga aparecem primeiro.",
                prioridade="baixa", secao=None,
            ))
        return s

    # --- Reescrita ---------------------------------------------------------------

    def reescrever(self, secao: str, texto: str, vaga: ContextoVaga | None) -> Reescrita:
        if secao == "competencias":
            novo, obs = _organizar_competencias(texto)
            return Reescrita(novo, obs)

        itens = _juntar_linhas_quebradas(texto)
        mudancas = 0
        saida = []
        for item in itens:
            if not item:
                saida.append("")
                continue
            prefixo = "• " if item.startswith("• ") else ""
            corpo, mudou = _reformular_item(item[len(prefixo):])
            mudancas += mudou
            saida.append(prefixo + corpo)

        observacoes = []
        if mudancas:
            observacoes.append(f"{mudancas} trecho(s) reescrito(s) para começar com verbo de ação, em primeira pessoa implícita.")
        if len(saida) != len(texto.splitlines()):
            observacoes.append("Linhas quebradas pelo PDF foram reunidas e os marcadores de lista, padronizados.")
        if secao in ("experiencia", "projetos"):
            sem_numero = [i for i in saida if i.startswith("• ") and not re.search(r"\d", i)]
            if sem_numero:
                observacoes.append(f"{len(sem_numero)} item(ns) sem números. Se tiver o dado, acrescente o resultado "
                                   "(%, tempo, volume). Não inclua números que você não possa comprovar.")
        if secao == "resumo" and vaga:
            citadas = [c for c in vaga.competencias_atendidas if TextoBusca(texto).buscar(c.lower())]
            faltam = [c for c in vaga.competencias_atendidas if c not in citadas]
            if faltam:
                observacoes.append(f"Você comprovou {', '.join(faltam[:5])} no currículo e a vaga pede. "
                                   "Considere mencioná-las no resumo.")
            if vaga.cargo and normalizar(vaga.cargo.split()[0]) not in normalizar(texto):
                observacoes.append(f"Considere citar o cargo de interesse ({vaga.cargo}).")
        observacoes.append("O modo local faz ajustes de forma e estrutura. Para uma reescrita completa do texto, "
                           "configure a chave do Gemini (veja o README).")
        return Reescrita("\n".join(saida).strip(), observacoes)


# =====================================================================================
# Provedor Gemini
# =====================================================================================

REGRAS_VERACIDADE = """Regras obrigatórias:
- Nunca invente experiências, empresas, cargos, datas, números, certificações, competências ou qualificações.
- Use somente fatos presentes no material fornecido. Se um dado (como um resultado numérico) faria a frase melhor, não o crie: oriente a pessoa a incluí-lo se ela tiver.
- Não recomende incluir uma competência que o currículo não mostra, a não ser condicionada a "se você tiver essa experiência".
- Não considere idade, gênero, raça, foto, endereço ou outras características pessoais.
- Escreva em português do Brasil, em tom profissional e direto, sem emojis."""

PROMPT_SUGESTOES = f"""Você é especialista em recrutamento e em currículos para sistemas ATS.
Recebe o resultado de uma análise de compatibilidade entre um currículo e uma vaga, já calculada por um motor determinístico.
O score já está definido: não o recalcule nem o comente.
Sua tarefa: escrever de 4 a 8 sugestões práticas e específicas para o candidato melhorar o currículo PARA ESTA VAGA,
citando os requisitos e trechos concretos da análise.

{REGRAS_VERACIDADE}"""

PROMPT_REESCRITA = f"""Você é especialista em escrita de currículos.
Reescreva a seção de currículo recebida para deixá-la mais clara, objetiva e profissional:
verbos de ação no início dos itens, frases curtas, sem pronomes de primeira pessoa, mantendo o formato de lista quando houver.
Você pode reorganizar e enxugar o texto. Pode usar os termos da vaga apenas para coisas que o texto original já mostra.

{REGRAS_VERACIDADE}

Em "observacoes", explique brevemente o que mudou e o que a pessoa poderia acrescentar (se tiver)."""


class _SugestoesGemini(BaseModel):
    sugestoes: list[Sugestao] = Field(min_length=1, max_length=10)


class _ReescritaGemini(BaseModel):
    texto: str
    observacoes: list[str]


class ErroProvedorIA(Exception):
    pass


class ProvedorGemini:
    nome = "gemini"

    def __init__(self, settings: Settings):
        from google import genai
        from google.genai import types

        self._types = types
        self._modelo = settings.gemini_model
        self._cliente = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=settings.ai_timeout_seconds * 1000),
        )

    def _gerar(self, sistema: str, conteudo: str, schema: type[BaseModel]) -> BaseModel:
        try:
            resposta = self._cliente.models.generate_content(
                model=self._modelo,
                contents=conteudo,
                config=self._types.GenerateContentConfig(
                    system_instruction=sistema,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.3,
                ),
            )
        except Exception as exc:
            raise ErroProvedorIA(f"Falha na chamada ao Gemini ({type(exc).__name__}).") from exc
        if resposta.parsed is None:
            raise ErroProvedorIA("O Gemini não devolveu uma resposta no formato esperado.")
        return resposta.parsed

    def gerar_sugestoes(self, resultado: ResultadoMatching, curriculo: CurriculoAnalisado) -> list[Sugestao]:
        contexto = {
            "vaga": resultado.vaga.model_dump(include={"cargo", "nivel", "anos_experiencia", "formacao", "idiomas"}),
            "score": resultado.score,
            "categorias": [{"categoria": c.rotulo, "score": c.score, "detalhe": c.detalhe} for c in resultado.categorias],
            "requisitos": [r.model_dump(include={"texto", "obrigatorio", "status", "justificativa"}) for r in resultado.requisitos],
            "palavras_chave": [p.model_dump(include={"termo_na_vaga", "status"}) for p in resultado.palavras_chave],
            "curriculo": {s.rotulo: s.texto[:2500] for s in curriculo.secoes if s.chave not in SECOES_IGNORADAS},
        }
        dados = self._gerar(PROMPT_SUGESTOES, json.dumps(contexto, ensure_ascii=False), _SugestoesGemini)
        return dados.sugestoes

    def reescrever(self, secao: str, texto: str, vaga: ContextoVaga | None) -> Reescrita:
        conteudo = {"secao": ROTULOS_SECAO_EDITOR.get(secao, secao), "texto_original": texto}
        if vaga:
            conteudo["vaga"] = {"cargo": vaga.cargo, "termos_da_vaga": vaga.termos_vaga[:20]}
        dados = self._gerar(PROMPT_REESCRITA, json.dumps(conteudo, ensure_ascii=False), _ReescritaGemini)
        return Reescrita(dados.texto.strip(), dados.observacoes)


# =====================================================================================
# Serviço
# =====================================================================================

def verificar_veracidade(original: str, sugerido: str) -> list[str]:
    """Aponta competências e números que aparecem na sugestão mas não no original."""
    alertas = []
    b_orig, b_sug = TextoBusca(original), TextoBusca(sugerido)
    novas = [
        c.nome for c in COMPETENCIAS
        if any(b_sug.buscar(s) for s in c.sinonimos) and not any(b_orig.buscar(s) for s in c.sinonimos)
    ]
    if novas:
        alertas.append(f"Atenção: a sugestão cita {', '.join(novas)}, que não aparece(m) no texto original. "
                       "Mantenha apenas se corresponder à sua experiência real.")
    numeros_novos = set(re.findall(r"\d+(?:[.,]\d+)?%?", sugerido)) - set(re.findall(r"\d+(?:[.,]\d+)?%?", original))
    if numeros_novos:
        alertas.append(f"Atenção: a sugestão contém números que não estavam no original ({', '.join(sorted(numeros_novos))}). "
                       "Confirme se são verdadeiros antes de usar.")
    return alertas


class ServicoIA:
    def __init__(self, provedor: ProvedorIA):
        self.provedor = provedor
        self.local = ProvedorLocal()

    def sugestoes(self, resultado: ResultadoMatching, curriculo: CurriculoAnalisado) -> tuple[list[Sugestao], str, str | None]:
        """Devolve (sugestões, fonte, aviso)."""
        if self.provedor.nome != "local":
            try:
                return self.provedor.gerar_sugestoes(resultado, curriculo), self.provedor.nome, None
            except ErroProvedorIA as exc:
                logger.warning("Sugestões via %s falharam: %s", self.provedor.nome, exc)
                aviso = f"Não foi possível gerar sugestões com {self.provedor.nome}; exibindo sugestões do modo local."
                return self.local.gerar_sugestoes(resultado, curriculo), "local", aviso
        return self.local.gerar_sugestoes(resultado, curriculo), "local", None

    def reescrever(self, secao: str, texto: str, vaga: ContextoVaga | None) -> tuple[Reescrita, str]:
        fonte = self.provedor.nome
        try:
            reescrita = self.provedor.reescrever(secao, texto, vaga)
        except ErroProvedorIA as exc:
            logger.warning("Reescrita via %s falhou: %s", fonte, exc)
            reescrita = self.local.reescrever(secao, texto, vaga)
            reescrita.observacoes.insert(0, f"Não foi possível usar {fonte}; esta é a versão do modo local.")
            fonte = "local"
        reescrita.observacoes.extend(verificar_veracidade(texto, reescrita.texto))
        return reescrita, fonte


def obter_provedor(settings: Settings | None = None) -> ProvedorIA:
    settings = settings or get_settings()
    escolha = settings.ai_provider.lower()
    if escolha == "gemini" or (escolha == "auto" and settings.gemini_api_key):
        if not settings.gemini_api_key:
            logger.warning("AI_PROVIDER=gemini, mas GEMINI_API_KEY não está definida. Usando o modo local.")
            return ProvedorLocal()
        try:
            return ProvedorGemini(settings)
        except Exception as exc:
            logger.warning("Não foi possível iniciar o Gemini (%s). Usando o modo local.", type(exc).__name__)
    return ProvedorLocal()


def obter_servico_ia() -> ServicoIA:
    return ServicoIA(obter_provedor())


def contexto_vaga(resultado_dict: dict) -> ContextoVaga:
    """Monta o contexto da vaga a partir de uma análise salva."""
    return ContextoVaga(
        cargo=resultado_dict["vaga"]["cargo"],
        competencias_atendidas=[
            c["nome"] for c in resultado_dict["competencias"] if c["status"] == "encontrada" and c["obrigatoria"]
        ],
        termos_vaga=[p["termo_na_vaga"] for p in resultado_dict["palavras_chave"]],
    )

