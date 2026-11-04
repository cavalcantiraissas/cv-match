"""Dependências injetáveis (substituídas nos testes)."""

from __future__ import annotations

from app.services.ai_service import ServicoIA, obter_servico_ia
from app.services.semantic import MotorSemantico, obter_motor


def motor_semantico() -> MotorSemantico:
    return obter_motor()


def servico_ia() -> ServicoIA:
    return obter_servico_ia()
