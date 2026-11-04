"""Schemas da API (contrato com o frontend)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

StatusRequisito = Literal["atendido", "parcial", "nao_identificado"]
StatusCompetencia = Literal["encontrada", "parcial", "nao_identificada"]
NivelEvidencia = Literal["forte", "listada", "relacionada", "semantica", "ausente"]


# --- Currículo ------------------------------------------------------------------

class SecaoCurriculo(BaseModel):
    chave: str
    rotulo: str
    texto: str


class CurriculoUploadResposta(BaseModel):
    resume_id: str
    nome_arquivo: str
    paginas: int
    caracteres: int
    secoes: list[SecaoCurriculo]
    previa: str
    avisos: list[str] = []


# --- Análise --------------------------------------------------------------------

class AnaliseRequisicao(BaseModel):
    resume_id: str = Field(min_length=1, max_length=64)
    descricao_vaga: str = Field(min_length=80, description="Descrição completa da vaga (mínimo de 80 caracteres).")


class CategoriaScore(BaseModel):
    chave: str
    rotulo: str
    peso: float = Field(description="Peso configurado (0 a 1).")
    peso_efetivo: float = Field(description="Peso após redistribuir categorias não aplicáveis.")
    score: float | None = Field(description="0 a 100; None quando a vaga não tem requisitos desta categoria.")
    aplicavel: bool
    contribuicao: float = Field(description="Pontos que a categoria soma ao score final.")
    detalhe: str


class CompetenciaAvaliada(BaseModel):
    nome: str
    tipo: Literal["tecnica", "ferramenta", "comportamental"]
    obrigatoria: bool
    status: StatusCompetencia
    evidencia: NivelEvidencia
    credito: float
    justificativa: str
    trecho: str | None = None


class RequisitoAvaliado(BaseModel):
    texto: str
    categoria: str
    obrigatorio: bool
    status: StatusRequisito
    credito: float
    justificativa: str
    trecho: str | None = None


class PalavraChave(BaseModel):
    termo: str
    termo_na_vaga: str
    obrigatoria: bool
    status: Literal["presente", "variacao", "ausente"]
    sugestao: str | None = None


class Sugestao(BaseModel):
    titulo: str
    descricao: str
    prioridade: Literal["alta", "media", "baixa"]
    secao: str | None = None


class VagaResumo(BaseModel):
    cargo: str
    nivel: str | None
    anos_experiencia: int | None
    formacao: str | None
    idiomas: list[str]
    competencias_tecnicas: list[str]
    ferramentas: list[str]
    competencias_comportamentais: list[str]
    certificacoes: list[str]
    diferenciais: list[str]
    responsabilidades: list[str]
    estruturada: bool


class CurriculoResumo(BaseModel):
    secoes: list[SecaoCurriculo]
    anos_experiencia: float | None
    anos_origem: str
    formacao: str
    idiomas: list[str]
    certificacoes: list[str]


class ResultadoAnalise(BaseModel):
    score: int
    classificacao: str
    categorias: list[CategoriaScore]
    competencias: list[CompetenciaAvaliada]
    requisitos: list[RequisitoAvaliado]
    palavras_chave: list[PalavraChave]
    sugestoes: list[Sugestao]
    fonte_sugestoes: str
    motor_semantico: str
    vaga: VagaResumo
    curriculo: CurriculoResumo
    avisos: list[str] = []


class AnaliseResposta(ResultadoAnalise):
    id: str
    criado_em: datetime
    descricao_vaga: str


class HistoricoItem(BaseModel):
    id: str
    cargo: str
    score: int
    classificacao: str
    criado_em: datetime


# --- Editor de currículo ------------------------------------------------------------

class MelhoriaRequisicao(BaseModel):
    secao: str = Field(min_length=1, max_length=40, description="Chave da seção (resumo, experiencia, projetos, competencias...).")
    texto: str = Field(min_length=10, max_length=8000)
    analysis_id: str | None = Field(default=None, description="Análise usada como contexto da vaga (opcional).")


class MelhoriaResposta(BaseModel):
    secao: str
    original: str
    sugerido: str
    observacoes: list[str]
    fonte: str
