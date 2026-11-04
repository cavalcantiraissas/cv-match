"""
Configuração central do CV Match.

Tudo que influencia o score fica aqui (pesos, créditos de evidência,
calibração semântica), para que a pontuação seja explicável e fácil de ajustar.
Variáveis de ambiente são lidas do arquivo `.env` na raiz do projeto ou do backend.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]

# Pesos de cada critério no score final (somam 1.0).
# Critérios sem nenhum requisito na vaga são excluídos e os pesos restantes
# são redistribuídos proporcionalmente (ver matching_engine.combinar_categorias).
PESOS_CATEGORIAS: dict[str, float] = {
    "competencias_tecnicas": 0.30,
    "experiencia": 0.25,
    "formacao": 0.15,
    "palavras_chave": 0.15,
    "competencias_comportamentais": 0.10,
    "idiomas_certificacoes": 0.05,
}

ROTULOS_CATEGORIAS: dict[str, str] = {
    "competencias_tecnicas": "Competências técnicas",
    "experiencia": "Experiência profissional",
    "formacao": "Formação acadêmica",
    "palavras_chave": "Palavras-chave e tecnologias",
    "competencias_comportamentais": "Competências comportamentais",
    "idiomas_certificacoes": "Idiomas e certificações",
}

# Crédito dado a uma competência conforme a força da evidência no currículo.
# Uma palavra isolada na lista de competências não vale o mesmo que o uso
# comprovado em uma experiência ou projeto.
CREDITO_EVIDENCIA: dict[str, float] = {
    "forte": 1.0,        # aparece em experiência, projeto ou certificação
    "listada": 0.6,      # aparece só na lista de competências ou no resumo
    "relacionada": 0.4,  # o currículo tem uma tecnologia equivalente/da mesma família
    "semantica": 0.4,    # trecho do currículo semanticamente próximo ao requisito
    "ausente": 0.0,
}

# Um requisito desejável conta com este peso relativo. Ele só entra no cálculo
# quando é atendido (nunca reduz o score; ver matching_engine.pontuar_itens).
PESO_DESEJAVEL = 0.5

CREDITO_MINIMO_ATENDIDO = 0.75   # crédito a partir do qual o requisito é "Atendido"
CREDITO_MINIMO_PARCIAL = 0.3     # abaixo disso é "Não identificado"

# Calibração da similaridade de cosseno para cada motor semântico:
# valores <= piso viram 0, valores >= teto viram 1, interpolação linear no meio.
# Faixas medidas com os currículos/vagas de tests/fixtures.py: frases sem relação
# ficam abaixo do piso e frases com o mesmo conteúdo, perto do teto.
CALIBRACAO_SEMANTICA: dict[str, tuple[float, float]] = {
    "sentence-transformers": (0.25, 0.65),
    "tfidf": (0.05, 0.35),
}
# Similaridade calibrada mínima para aceitar um trecho como evidência semântica
# parcial, e a partir da qual o trecho é considerado equivalente ao requisito.
LIMIAR_EVIDENCIA_SEMANTICA = 0.55
LIMIAR_SEMANTICA_FORTE = 0.9

FAIXAS_CLASSIFICACAO: list[tuple[int, str]] = [
    (90, "Excelente compatibilidade"),
    (75, "Boa compatibilidade"),
    (60, "Compatibilidade moderada"),
    (40, "Baixa compatibilidade"),
    (0, "Compatibilidade muito baixa"),
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = f"sqlite:///{BACKEND_DIR / 'cv_match.db'}"
    max_pdf_mb: float = 5.0
    max_pdf_pages: int = 10
    max_job_chars: int = 20_000
    # Currículos enviados e ainda não analisados são apagados após este prazo.
    resume_ttl_hours: int = 24
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # auto: usa Sentence Transformers se estiver instalado, senão TF-IDF.
    semantic_backend: str = "auto"  # auto | sentence-transformers | tfidf
    semantic_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # auto: usa Gemini se houver GEMINI_API_KEY, senão o provedor local.
    ai_provider: str = "auto"  # auto | gemini | local
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
    ai_timeout_seconds: int = 60

    @property
    def max_pdf_bytes(self) -> int:
        return int(self.max_pdf_mb * 1024 * 1024)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
