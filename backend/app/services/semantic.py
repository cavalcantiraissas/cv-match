"""
Motor de similaridade semântica.

Duas implementações com a mesma interface:
- `SentenceTransformerMotor`: embeddings multilíngues (entende sinônimos e
  paráfrases, ex.: "liderei um time" ~ "experiência com gestão de equipes").
- `TfidfMotor`: TF-IDF com n-gramas de caracteres (scikit-learn). Leve e sem
  downloads; captura variações de escrita, mas não paráfrases.

Os dois são determinísticos. O nome do motor usado fica registrado em cada
análise, porque a pontuação semântica depende dele.
"""

from __future__ import annotations

import logging
import threading
from typing import Protocol

import numpy as np

from app.core.config import CALIBRACAO_SEMANTICA, get_settings

logger = logging.getLogger(__name__)


class MotorSemantico(Protocol):
    nome: str

    def similaridade(self, a: list[str], b: list[str]) -> np.ndarray:
        """Matriz len(a) x len(b) com a similaridade de cosseno."""


class TfidfMotor:
    nome = "tfidf"

    def similaridade(self, a: list[str], b: list[str]) -> np.ndarray:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        from app.services.text_utils import normalizar

        if not a or not b:
            return np.zeros((len(a), len(b)))
        vetorizador = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        matriz = vetorizador.fit_transform([normalizar(t) for t in a + b])
        return cosine_similarity(matriz[: len(a)], matriz[len(a):])


class SentenceTransformerMotor:
    nome = "sentence-transformers"

    def __init__(self, modelo: str):
        from sentence_transformers import SentenceTransformer

        self._modelo = SentenceTransformer(modelo, device="cpu")

    def similaridade(self, a: list[str], b: list[str]) -> np.ndarray:
        if not a or not b:
            return np.zeros((len(a), len(b)))
        va = self._modelo.encode(a, normalize_embeddings=True, convert_to_numpy=True)
        vb = self._modelo.encode(b, normalize_embeddings=True, convert_to_numpy=True)
        return np.clip(va @ vb.T, -1.0, 1.0)


_motor: MotorSemantico | None = None
_trava = threading.Lock()


def obter_motor() -> MotorSemantico:
    """Motor único do processo, criado na primeira chamada (seguro entre threads)."""
    global _motor
    with _trava:
        if _motor is None:
            _motor = _criar_motor()
        return _motor


def _criar_motor() -> MotorSemantico:
    """Escolhe o motor conforme SEMANTIC_BACKEND (auto | sentence-transformers | tfidf)."""
    settings = get_settings()
    escolha = settings.semantic_backend.lower()
    if escolha in ("auto", "sentence-transformers"):
        try:
            motor = SentenceTransformerMotor(settings.semantic_model)
            logger.info("Motor semântico: sentence-transformers (%s)", settings.semantic_model)
            return motor
        except Exception as exc:  # pacote ausente, modelo sem download, etc.
            if escolha == "sentence-transformers":
                raise
            logger.warning("Sentence Transformers indisponível (%s). Usando TF-IDF.", type(exc).__name__)
    logger.info("Motor semântico: tfidf")
    return TfidfMotor()


def calibrar(valor: float, motor: str) -> float:
    """Converte cosseno bruto em 0..1 usando a faixa típica de cada motor."""
    piso, teto = CALIBRACAO_SEMANTICA[motor]
    return float(np.clip((valor - piso) / (teto - piso), 0.0, 1.0))
