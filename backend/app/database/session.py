"""Conexão com o SQLite via SQLAlchemy."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def criar_engine(url: str):
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _ativar_fk(conexao, _):
            # SQLite só respeita ON DELETE CASCADE com foreign_keys ligado.
            conexao.execute("PRAGMA foreign_keys=ON")
    return engine


engine = criar_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas() -> None:
    from app.models import entities  # noqa: F401  (registra os modelos)

    Base.metadata.create_all(bind=engine)
