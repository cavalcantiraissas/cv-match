"""Configuração dos testes: banco temporário, motor TF-IDF e IA local (sem rede)."""

import os
import tempfile

# Precisa vir antes de importar a aplicação (as configurações são lidas no import).
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/cv_match_test.db"
os.environ["SEMANTIC_BACKEND"] = "tfidf"
os.environ["AI_PROVIDER"] = "local"
os.environ["GEMINI_API_KEY"] = ""

from datetime import date  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.services.semantic import TfidfMotor  # noqa: E402

HOJE = date(2026, 11, 1)


@pytest.fixture(scope="session", params=["tfidf", "sentence-transformers"])
def motor(request):
    """Os testes do motor rodam com os dois motores semânticos (o 2º só se estiver instalado)."""
    if request.param == "tfidf":
        return TfidfMotor()
    pytest.importorskip("sentence_transformers")
    from app.core.config import get_settings
    from app.services.semantic import SentenceTransformerMotor

    try:
        return SentenceTransformerMotor(get_settings().semantic_model)
    except Exception as exc:  # modelo não baixado e sem internet
        pytest.skip(f"Modelo do Sentence Transformers indisponível: {type(exc).__name__}")


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c
