"""Aplicação FastAPI do CV Match. Documentação interativa em /docs."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analysis, resumes
from app.core.config import PESOS_CATEGORIAS, ROTULOS_CATEGORIAS, get_settings
from app.database.session import SessionLocal, criar_tabelas
from app.services.ai_service import obter_provedor
from app.services.semantic import obter_motor

VERSAO = "1.0.0"

# Os logs registram apenas eventos e tipos de erro, nunca o conteúdo de currículos ou vagas.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cv_match")


@asynccontextmanager
async def lifespan(_: FastAPI):
    criar_tabelas()
    with SessionLocal() as db:
        resumes.limpar_expirados(db)
    # Carrega o modelo semântico em segundo plano para a 1ª análise não esperar o download/carregamento.
    threading.Thread(target=obter_motor, daemon=True).start()
    yield


app = FastAPI(
    title="CV Match API",
    version=VERSAO,
    description=(
        "Analisa a compatibilidade entre um currículo em PDF e a descrição de uma vaga. "
        "O score é calculado por regras determinísticas e similaridade semântica; a IA generativa "
        "(opcional) só gera sugestões e reescritas."
    ),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
app.include_router(resumes.router)
app.include_router(analysis.router)


@app.exception_handler(Exception)
async def erro_inesperado(_: Request, exc: Exception):
    logger.error("Erro inesperado: %s", type(exc).__name__, exc_info=False)
    return JSONResponse(status_code=500, content={"detail": {
        "codigo": "erro_interno", "mensagem": "Ocorreu um erro inesperado ao processar a solicitação. Tente novamente."}})


@app.get("/api/health", tags=["Sistema"], summary="Verifica o funcionamento da aplicação")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "versao": VERSAO,
        "motor_semantico": obter_motor().nome,
        "provedor_ia": obter_provedor(settings).nome,
    }


@app.get("/api/config", tags=["Sistema"], summary="Pesos do score e limites de upload")
def config():
    settings = get_settings()
    return {
        "pesos": [{"chave": k, "rotulo": ROTULOS_CATEGORIAS[k], "peso": v} for k, v in PESOS_CATEGORIAS.items()],
        "max_pdf_mb": settings.max_pdf_mb,
        "max_pdf_paginas": settings.max_pdf_pages,
        "max_vaga_caracteres": settings.max_job_chars,
        "provedor_ia": obter_provedor(settings).nome,
    }
