"""
Motor de compatibilidade currículo x vaga.

O score é calculado só com regras determinísticas e similaridade semântica:
mesma entrada e mesmo motor semântico produzem sempre o mesmo resultado, e cada
ponto pode ser rastreado até um requisito e um trecho do currículo. A IA
generativa não participa desta etapa.

Visão geral:
1. Cada competência pedida recebe um crédito conforme a evidência no currículo
   (CREDITO_EVIDENCIA em core/config.py).
2. Cada categoria tem um score 0-100 calculado a partir dos créditos dos seus
   itens; itens desejáveis só entram quando atendidos (pontuar_itens).
3. O score final é a média ponderada das categorias aplicáveis (PESOS_CATEGORIAS),
   com os pesos redistribuídos quando a vaga não tem requisitos de uma categoria.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.catalogo import AREAS_FORMACAO, COMPETENCIA_POR_NOME, GRUPOS_PROXIMOS, ROTULO_NIVEL_IDIOMA
from app.core.config import (
    CREDITO_EVIDENCIA,
    CREDITO_MINIMO_ATENDIDO,
    CREDITO_MINIMO_PARCIAL,
    FAIXAS_CLASSIFICACAO,
    LIMIAR_EVIDENCIA_SEMANTICA,
    LIMIAR_SEMANTICA_FORTE,
    PESO_DESEJAVEL,
    PESOS_CATEGORIAS,
    ROTULOS_CATEGORIAS,
)
from app.schemas.analysis import (
    CategoriaScore,
    CompetenciaAvaliada,
    CurriculoResumo,
    PalavraChave,
    RequisitoAvaliado,
    SecaoCurriculo,
    VagaResumo,
)
from app.services.job_analyzer import RequisitoVaga, VagaAnalisada
from app.services.resume_analyzer import ROTULO_SECAO, SECOES_PRATICA, CurriculoAnalisado
from app.services.semantic import MotorSemantico, calibrar
from app.services.text_utils import TextoBusca

CATEGORIA_POR_TIPO = {
    "competencia": "competencias_tecnicas",
    "comportamental": "competencias_comportamentais",
    "experiencia": "experiencia",
    "formacao": "formacao",
    "idioma": "idiomas_certificacoes",
    "certificacao": "idiomas_certificacoes",
    "outro": "experiencia",
}


@dataclass
class Avaliacao:
    credito: float
    evidencia: str  # nível de evidência (chave de CREDITO_EVIDENCIA)
    justificativa: str
    trecho: str | None = None


@dataclass
class ResultadoMatching:
    score: int
    classificacao: str
    categorias: list[CategoriaScore]
    competencias: list[CompetenciaAvaliada]
    requisitos: list[RequisitoAvaliado]
    palavras_chave: list[PalavraChave]
    vaga: VagaResumo
    curriculo: CurriculoResumo
    avisos: list[str]
    motor_semantico: str


def classificar(score: float) -> str:
    return next(rotulo for minimo, rotulo in FAIXAS_CLASSIFICACAO if score >= minimo)


def status_por_credito(credito: float) -> str:
    if credito >= CREDITO_MINIMO_ATENDIDO:
        return "atendido"
    if credito >= CREDITO_MINIMO_PARCIAL:
        return "parcial"
    return "nao_identificado"


def pontuar_itens(itens: list[tuple[float, bool]]) -> float | None:
    """
    Score 0..1 de uma categoria a partir de (crédito, obrigatório).

    Obrigatórios entram sempre. Desejáveis entram com PESO_DESEJAVEL e somente
    na medida em que foram atendidos (crédito soma no numerador e no denominador),
    então podem aumentar o score, mas nunca reduzi-lo.
    Sem itens obrigatórios a categoria não é aplicável (devolve None).
    """
    obrigatorios = [c for c, o in itens if o]
    desejaveis = [c for c, o in itens if not o]
    if not obrigatorios:
        return None
    bonus = PESO_DESEJAVEL * sum(desejaveis)
    return (sum(obrigatorios) + bonus) / (len(obrigatorios) + bonus)


class MotorCompatibilidade:
    def __init__(self, curriculo: CurriculoAnalisado, vaga: VagaAnalisada, motor: MotorSemantico):
        self.cv = curriculo
        self.vaga = vaga
        self.motor = motor
        self.avisos: list[str] = []
        self.busca_cv = TextoBusca(curriculo.texto_profissional())
        self._frases = [f for _, f in curriculo.frases]
        self._secao_frase = [s for s, _ in curriculo.frases]
        self._cache_comp: dict[str, Avaliacao] = {}

    # --- Similaridade semântica -------------------------------------------------

    def _melhores_frases(self, consultas: list[str], secoes: set[str] | None = None) -> list[tuple[float, str | None]]:
        """Para cada consulta, a frase do currículo mais parecida (similaridade calibrada 0..1)."""
        indices = [i for i, s in enumerate(self._secao_frase) if secoes is None or s in secoes]
        if not consultas or not indices:
            return [(0.0, None)] * len(consultas)
        frases = [self._frases[i] for i in indices]
        matriz = self.motor.similaridade(consultas, frases)
        resultado = []
        for linha in matriz:
            j = int(np.argmax(linha))
            resultado.append((calibrar(float(linha[j]), self.motor.nome), frases[j]))
        return resultado

    # --- Competências -------------------------------------------------------------

    def avaliar_competencia(self, nome: str) -> Avaliacao:
        if nome in self._cache_comp:
            return self._cache_comp[nome]
        ev = self.cv.competencias.get(nome)
        if ev and ev.nivel == "forte":
            origem = f" (comprovado pelo uso de {ev.inferida_de})" if ev.inferida_de else ""
            av = Avaliacao(
                CREDITO_EVIDENCIA["forte"], "forte",
                f"Evidenciado na seção {ROTULO_SECAO.get(ev.secao, ev.secao)}{origem}.", ev.trecho,
            )
        elif ev:
            origem = f" (inferido de {ev.inferida_de})" if ev.inferida_de else ""
            av = Avaliacao(
                CREDITO_EVIDENCIA["listada"], "listada",
                f"Aparece em {ROTULO_SECAO.get(ev.secao, ev.secao)}{origem}, mas sem uma experiência ou "
                "projeto que mostre como foi aplicado.", ev.trecho,
            )
        else:
            av = self._avaliar_relacionada(nome)
        self._cache_comp[nome] = av
        return av

    def _avaliar_relacionada(self, nome: str) -> Avaliacao:
        familia = COMPETENCIA_POR_NOME[nome].familia
        if familia:
            parecidas = [
                ev for n, ev in self.cv.competencias.items()
                if n != nome and COMPETENCIA_POR_NOME[n].familia == familia and not ev.inferida_de
            ]
            if parecidas:
                ev = max(parecidas, key=lambda e: (e.nivel == "forte", e.ocorrencias))
                return Avaliacao(
                    CREDITO_EVIDENCIA["relacionada"], "relacionada",
                    f"Não citado diretamente, mas o currículo mostra {ev.nome}, tecnologia equivalente "
                    "ou da mesma família.", ev.trecho,
                )
        return Avaliacao(0.0, "ausente", "Não encontrado no currículo.")

    # --- Requisitos -----------------------------------------------------------------

    def avaliar_requisito(self, req: RequisitoVaga, semantica: tuple[float, str | None]) -> Avaliacao:
        if req.tipo == "idioma" and req.idioma:
            return self._avaliar_idioma(*req.idioma)
        if req.tipo == "formacao" and req.formacao:
            return self._avaliar_formacao(req.formacao)
        if req.tipo == "certificacao":
            return self._avaliar_certificacao(req)

        partes: list[Avaliacao] = []
        if req.tipo == "experiencia" and req.anos:
            partes.append(self._avaliar_anos(req.anos, "a vaga"))
        if req.competencias:
            avs = [(n, self.avaliar_competencia(n)) for n in req.competencias]
            if req.alternativas:
                nome, melhor = max(avs, key=lambda x: x[1].credito)
                partes.append(Avaliacao(melhor.credito, melhor.evidencia, f"{nome}: {melhor.justificativa}", melhor.trecho))
            else:
                credito = sum(a.credito for _, a in avs) / len(avs)
                justificativa = " ".join(f"{n}: {a.justificativa}" for n, a in avs)
                trecho = next((a.trecho for _, a in avs if a.trecho), None)
                nivel = min((a.evidencia for _, a in avs), key=lambda e: CREDITO_EVIDENCIA[e])
                partes.append(Avaliacao(credito, nivel, justificativa, trecho))
        if partes:
            credito = sum(p.credito for p in partes) / len(partes)
            return Avaliacao(credito, partes[-1].evidencia, " ".join(p.justificativa for p in partes),
                             next((p.trecho for p in partes if p.trecho), None))
        return self._avaliar_semantica(semantica)

    def _avaliar_semantica(self, semantica: tuple[float, str | None]) -> Avaliacao:
        similaridade, frase = semantica
        if frase and similaridade >= LIMIAR_SEMANTICA_FORTE:
            return Avaliacao(0.8, "semantica", f"Trecho do currículo muito semelhante ao requisito (similaridade {similaridade:.0%}).", frase)
        if frase and similaridade >= LIMIAR_EVIDENCIA_SEMANTICA:
            return Avaliacao(
                CREDITO_EVIDENCIA["semantica"], "semantica",
                f"Há um trecho relacionado (similaridade {similaridade:.0%}), mas sem menção direta ao requisito.", frase,
            )
        return Avaliacao(0.0, "ausente", "Nenhum trecho do currículo trata deste requisito.")

    def anos_candidato(self) -> tuple[float | None, str]:
        if self.cv.anos_experiencia is not None:
            return self.cv.anos_experiencia, "calculado a partir dos períodos das experiências"
        if self.cv.anos_declarados is not None:
            return self.cv.anos_declarados, "declarado no currículo"
        return None, "não identificado"

    def _avaliar_anos(self, exigidos: int, origem: str) -> Avaliacao:
        anos, como = self.anos_candidato()
        if anos is None:
            return Avaliacao(0.0, "ausente", f"{origem.capitalize()} pede {exigidos}+ anos, mas não encontramos períodos "
                             "(ex.: 'jan/2020 – atual') nas experiências para calcular o tempo de atuação.")
        credito = min(1.0, anos / exigidos) if exigidos else 1.0
        return Avaliacao(credito, "forte" if credito >= 1 else "listada",
                         f"{origem.capitalize()} pede {exigidos}+ anos; o currículo soma {anos:.1f} anos ({como}).")

    def _avaliar_idioma(self, idioma: str, nivel_min: int | None) -> Avaliacao:
        encontrado = self.cv.idiomas.get(idioma)
        exigido = f" nível {ROTULO_NIVEL_IDIOMA[nivel_min].lower()}" if nivel_min else ""
        if not encontrado:
            return Avaliacao(0.0, "ausente", f"A vaga pede {idioma}{exigido}, que não aparece no currículo.")
        if nivel_min is None:
            return Avaliacao(1.0, "forte", f"{idioma} informado ({encontrado.rotulo.lower()}).", encontrado.trecho)
        if encontrado.nivel is None:
            return Avaliacao(0.5, "listada", f"{idioma} aparece, mas sem nível. A vaga pede{exigido}.", encontrado.trecho)
        if encontrado.nivel >= nivel_min:
            return Avaliacao(1.0, "forte", f"{idioma} {encontrado.rotulo.lower()} atende ao{exigido} pedido.", encontrado.trecho)
        credito = 0.5 if nivel_min - encontrado.nivel == 1 else 0.2
        return Avaliacao(credito, "listada", f"{idioma} {encontrado.rotulo.lower()}, abaixo do{exigido} pedido.", encontrado.trecho)

    def _avaliar_formacao(self, exigida: dict) -> Avaliacao:
        f = self.cv.formacao
        if f.nivel == 0:
            return Avaliacao(0.0, "ausente", f"A vaga pede {exigida['rotulo'].lower()}, e não identificamos formação no currículo.")
        if f.nivel_concluido >= exigida["nivel"]:
            credito, situacao = 1.0, f"{f.rotulo} concluída atende ao nível pedido ({exigida['rotulo'].lower()})."
        elif f.nivel >= exigida["nivel"]:
            credito = 1.0 if exigida["aceita_cursando"] else 0.6
            situacao = f"{f.rotulo} em andamento; a vaga pede {exigida['rotulo'].lower()}" + (
                " e aceita formação em curso." if exigida["aceita_cursando"] else " concluída."
            )
        else:
            credito = 0.4 if exigida["nivel"] - f.nivel == 1 else 0.1
            situacao = f"Formação identificada ({f.rotulo.lower()}) abaixo do nível pedido ({exigida['rotulo'].lower()})."

        if exigida["areas"] and credito > 0:
            if set(exigida["areas"]) & set(f.areas):
                situacao += " Área compatível."
            else:
                grupos_vaga = {AREAS_FORMACAO[a][0] for a in exigida["areas"]}
                grupos_cv = {AREAS_FORMACAO[a][0] for a in f.areas}
                proximos = set().union(*(GRUPOS_PROXIMOS.get(g, set()) | {g} for g in grupos_vaga))
                if exigida["afins"] and grupos_cv & proximos:
                    credito *= 0.9
                    situacao += f" Área ({', '.join(f.areas)}) aceita como afim."
                elif f.areas:
                    credito *= 0.5
                    situacao += f" Área diferente da pedida ({', '.join(exigida['areas'])})."
                else:
                    credito *= 0.7
                    situacao += " Não identificamos a área do curso."
        return Avaliacao(credito, "forte" if credito >= CREDITO_MINIMO_ATENDIDO else "listada", situacao, f.trecho or None)

    def _avaliar_certificacao(self, req: RequisitoVaga) -> Avaliacao:
        for nome in req.certificacoes:
            if nome in self.cv.certificacoes:
                return Avaliacao(1.0, "forte", f"Certificação {nome} encontrada.", self.cv.certificacoes[nome])
        if req.competencias:
            av = [self.avaliar_competencia(n) for n in req.competencias]
            if any(a.credito > 0 for a in av):
                return Avaliacao(0.3, "relacionada", "Não encontramos a certificação, mas o currículo mostra experiência "
                                 f"com {', '.join(req.competencias)}.", next((a.trecho for a in av if a.trecho), None))
        return Avaliacao(0.0, "ausente", "Certificação não encontrada no currículo.")

    # --- Categorias -------------------------------------------------------------------

    def _score_experiencia(self, relevancia: float | None) -> tuple[float | None, str]:
        exigidos, origem = self.vaga.anos_experiencia, "a vaga"
        if exigidos is None and self.vaga.anos_tipicos_nivel:
            exigidos, origem = self.vaga.anos_tipicos_nivel, f"o nível {self.vaga.nivel} (estimativa)"
        partes, detalhes = [], []
        if exigidos:
            av = self._avaliar_anos(exigidos, origem)
            partes.append((0.6, av.credito))
            detalhes.append(av.justificativa)
        if relevancia is not None:
            partes.append((0.4, relevancia))
            detalhes.append(f"Aderência das experiências às atividades da vaga: {relevancia:.0%}.")
        if not partes:
            return None, "A vaga não informa tempo de experiência nem atividades."
        total = sum(p for p, _ in partes)
        return sum(p * v for p, v in partes) / total, " ".join(detalhes)

    def _palavras_chave(self) -> list[PalavraChave]:
        resultado = []
        for p in self.vaga.palavras_chave:
            if self.busca_cv.buscar(p.termo):
                status, sugestao = "presente", None
            elif p.no_catalogo and p.nome in self.cv.competencias and not self.cv.competencias[p.nome].inferida_de:
                ev = self.cv.competencias[p.nome]
                status = "variacao"
                sugestao = (f"A vaga escreve “{p.termo}”. Seu currículo cita a mesma competência de outra forma "
                            f"({ev.trecho}). Usar o termo exato da vaga ajuda na leitura por sistemas ATS.")
            else:
                status = "ausente"
                relacionada = self._avaliar_relacionada(p.nome) if p.no_catalogo else None
                if relacionada and relacionada.evidencia == "relacionada":
                    sugestao = (f"Você mostra experiência com tecnologia equivalente. Se também já usou {p.nome}, "
                                "cite explicitamente onde e como.")
                else:
                    sugestao = f"Inclua “{p.termo}” somente se você realmente tiver experiência com isso."
            resultado.append(PalavraChave(termo=p.nome, termo_na_vaga=p.termo, obrigatoria=p.obrigatoria,
                                          status=status, sugestao=sugestao))
        return resultado

    def calcular(self) -> ResultadoMatching:
        vaga = self.vaga
        consultas = [r.texto for r in vaga.requisitos]
        semanticas = self._melhores_frases(consultas)

        requisitos: list[RequisitoAvaliado] = []
        for req, sem in zip(vaga.requisitos, semanticas):
            av = self.avaliar_requisito(req, sem)
            requisitos.append(RequisitoAvaliado(
                texto=req.texto, categoria=CATEGORIA_POR_TIPO[req.tipo], obrigatorio=req.obrigatorio,
                status=status_por_credito(av.credito), credito=round(av.credito, 3),
                justificativa=av.justificativa, trecho=av.trecho,
            ))

        competencias: list[CompetenciaAvaliada] = []
        for comp in vaga.competencias.values():
            av = self.avaliar_competencia(comp.nome)
            status = "encontrada" if av.credito >= CREDITO_MINIMO_ATENDIDO else ("parcial" if av.credito > 0 else "nao_identificada")
            competencias.append(CompetenciaAvaliada(
                nome=comp.nome, tipo=comp.tipo, obrigatoria=comp.obrigatoria, status=status, evidencia=av.evidencia,
                credito=av.credito, justificativa=av.justificativa, trecho=av.trecho,
            ))

        # Aderência das experiências: cada atividade da vaga comparada às frases de experiência/projetos.
        # Sem lista de atividades, os próprios requisitos descrevem o trabalho esperado.
        atividades = vaga.responsabilidades or [
            r.texto for r in vaga.requisitos if r.tipo not in ("idioma", "formacao", "certificacao")
        ]
        relevancia = None
        if atividades:
            secoes = SECOES_PRATICA if any(s in SECOES_PRATICA for s in self._secao_frase) else None
            melhores = self._melhores_frases(atividades, secoes)
            relevancia = float(np.mean([s for s, _ in melhores]))

        palavras = self._palavras_chave()
        scores: dict[str, tuple[float | None, str]] = {}

        def itens_comp(tipos: set[str]) -> list[tuple[float, bool]]:
            return [(c.credito, c.obrigatoria) for c in competencias if c.tipo in tipos]

        tecnicas = itens_comp({"tecnica", "ferramenta"})
        scores["competencias_tecnicas"] = (pontuar_itens(tecnicas), self._detalhe_itens(tecnicas, "competências técnicas e ferramentas"))
        comport = itens_comp({"comportamental"})
        scores["competencias_comportamentais"] = (pontuar_itens(comport), self._detalhe_itens(comport, "competências comportamentais"))
        scores["experiencia"] = self._score_experiencia(relevancia)

        credito_palavra = {"presente": 1.0, "variacao": 0.75, "ausente": 0.0}
        itens_palavras = [(credito_palavra[p.status], p.obrigatoria) for p in palavras]
        presentes = sum(1 for p in palavras if p.status == "presente")
        scores["palavras_chave"] = (pontuar_itens(itens_palavras),
                                    f"{presentes} de {len(palavras)} termos da vaga aparecem exatamente como escritos.")

        formacao = [(r.credito, r.obrigatorio) for r in requisitos if r.categoria == "formacao"]
        scores["formacao"] = (pontuar_itens(formacao),
                              next((r.justificativa for r in requisitos if r.categoria == "formacao"), "A vaga não pede formação específica."))

        idiomas_cert = [(r.credito, r.obrigatorio) for r in requisitos if r.categoria == "idiomas_certificacoes"]
        scores["idiomas_certificacoes"] = (pontuar_itens(idiomas_cert), self._detalhe_itens(idiomas_cert, "requisitos de idioma/certificação"))

        # Requisitos sem competência do catálogo ("outro") entram na experiência.
        outros = [(r.credito, r.obrigatorio) for r, req in zip(requisitos, vaga.requisitos) if req.tipo == "outro"]
        if outros and scores["experiencia"][0] is not None:
            media_outros = pontuar_itens(outros)
            if media_outros is not None:
                base, detalhe = scores["experiencia"]
                scores["experiencia"] = (0.75 * base + 0.25 * media_outros,
                                         detalhe + f" Requisitos descritivos avaliados por similaridade: {media_outros:.0%}.")

        categorias = self._combinar(scores)
        score = round(sum(c.contribuicao for c in categorias))
        if not any(c.aplicavel for c in categorias):
            self.avisos.append("Não identificamos requisitos obrigatórios na descrição da vaga; por isso o score é 0. "
                               "Verifique se o texto inclui a seção de requisitos.")
        if not vaga.estruturada:
            self.avisos.append("A descrição não tem seções como 'Requisitos' ou 'Diferenciais'. Todos os itens "
                               "identificados foram tratados como obrigatórios, exceto os marcados como desejáveis.")
        if self.cv.anos_experiencia is None:
            self.avisos.append("Não encontramos períodos nas experiências (ex.: 'mar/2021 – atual'), então o tempo de "
                               "experiência não pôde ser calculado.")

        return ResultadoMatching(
            score=score, classificacao=classificar(score), categorias=categorias, competencias=competencias,
            requisitos=requisitos, palavras_chave=palavras, vaga=self._resumo_vaga(), curriculo=self._resumo_curriculo(),
            avisos=self.avisos, motor_semantico=self.motor.nome,
        )

    @staticmethod
    def _detalhe_itens(itens: list[tuple[float, bool]], nome: str) -> str:
        obrig = [c for c, o in itens if o]
        if not itens:
            return f"A vaga não cita {nome}."
        if not obrig:
            return f"A vaga cita apenas {nome} desejáveis; elas não alteram o score."
        atendidos = sum(1 for c in obrig if c >= CREDITO_MINIMO_ATENDIDO)
        parciais = sum(1 for c in obrig if CREDITO_MINIMO_PARCIAL <= c < CREDITO_MINIMO_ATENDIDO)
        return f"{atendidos} de {len(obrig)} obrigatórias evidenciadas" + (f", {parciais} parcialmente." if parciais else ".")

    @staticmethod
    def _combinar(scores: dict[str, tuple[float | None, str]]) -> list[CategoriaScore]:
        aplicaveis = {k: v for k, (v, _) in scores.items() if v is not None}
        total_pesos = sum(PESOS_CATEGORIAS[k] for k in aplicaveis)
        categorias = []
        for chave, peso in PESOS_CATEGORIAS.items():
            valor, detalhe = scores[chave]
            efetivo = peso / total_pesos if valor is not None and total_pesos else 0.0
            categorias.append(CategoriaScore(
                chave=chave, rotulo=ROTULOS_CATEGORIAS[chave], peso=peso, peso_efetivo=round(efetivo, 4),
                score=round(valor * 100, 1) if valor is not None else None, aplicavel=valor is not None,
                contribuicao=round(efetivo * valor * 100, 2) if valor is not None else 0.0, detalhe=detalhe,
            ))
        return categorias

    def _resumo_vaga(self) -> VagaResumo:
        v = self.vaga
        comps = v.competencias.values()
        idiomas = [f"{n}{' (' + ROTULO_NIVEL_IDIOMA[nv].lower() + ')' if nv else ''}{'' if o else ' – desejável'}"
                   for n, (nv, o) in v.idiomas.items()]
        formacao = None
        if v.formacao:
            formacao = v.formacao["rotulo"] + (f" em {', '.join(v.formacao['areas'])}" if v.formacao["areas"] else "") + (
                " ou áreas afins" if v.formacao["afins"] else "")
        return VagaResumo(
            cargo=v.cargo, nivel=v.nivel, anos_experiencia=v.anos_experiencia, formacao=formacao, idiomas=idiomas,
            competencias_tecnicas=[c.nome for c in comps if c.tipo == "tecnica"],
            ferramentas=[c.nome for c in comps if c.tipo == "ferramenta"],
            competencias_comportamentais=[c.nome for c in comps if c.tipo == "comportamental"],
            certificacoes=list(v.certificacoes),
            diferenciais=[r.texto for r in v.requisitos if not r.obrigatorio],
            responsabilidades=v.responsabilidades[:15], estruturada=v.estruturada,
        )

    def _resumo_curriculo(self) -> CurriculoResumo:
        anos, origem = self.anos_candidato()
        f = self.cv.formacao
        return CurriculoResumo(
            secoes=[SecaoCurriculo(chave=s.chave, rotulo=s.rotulo, texto=s.texto) for s in self.cv.secoes],
            anos_experiencia=anos, anos_origem=origem,
            formacao=f.rotulo + (" (em andamento)" if f.em_andamento else "") + (f" – {', '.join(f.areas)}" if f.areas else ""),
            idiomas=[f"{i.nome} ({i.rotulo.lower()})" for i in self.cv.idiomas.values()],
            certificacoes=list(self.cv.certificacoes),
        )


def calcular_compatibilidade(curriculo: CurriculoAnalisado, vaga: VagaAnalisada, motor: MotorSemantico) -> ResultadoMatching:
    return MotorCompatibilidade(curriculo, vaga, motor).calcular()
