"""
Tabelas do banco.

O PDF original nunca é salvo: guardamos apenas o texto extraído, já sem dados
de contato e características pessoais. Currículos sem análise expiram após
RESUME_TTL_HOURS; ao excluir uma análise, o currículo associado também é
excluído se nenhuma outra análise o usar.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return uuid.uuid4().hex


class Curriculo(Base):
    __tablename__ = "curriculos"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    paginas: Mapped[int] = mapped_column(Integer)
    texto: Mapped[str] = mapped_column(Text)

    analises: Mapped[list[Analise]] = relationship(back_populates="curriculo", cascade="all, delete-orphan", passive_deletes=True)


class Analise(Base):
    __tablename__ = "analises"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora, index=True)
    curriculo_id: Mapped[str] = mapped_column(ForeignKey("curriculos.id", ondelete="CASCADE"), index=True)
    cargo: Mapped[str] = mapped_column(String(255))
    score: Mapped[int] = mapped_column(Integer)
    classificacao: Mapped[str] = mapped_column(String(64))
    descricao_vaga: Mapped[str] = mapped_column(Text)
    resultado: Mapped[dict] = mapped_column(JSON)
    duracao_segundos: Mapped[float] = mapped_column(Float, default=0.0)

    curriculo: Mapped[Curriculo] = relationship(back_populates="analises")
