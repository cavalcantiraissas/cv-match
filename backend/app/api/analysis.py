"""Rotas de análise: comparar currículo x vaga, histórico e exclusão."""

from __future__ import annotations

import time
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import motor_semantico, servico_ia
from app.core.config import get_settings
from app.database.session import get_db
from app.models.entities import Analise, Curriculo
from app.schemas.analysis import AnaliseRequisicao, AnaliseResposta, HistoricoItem, ResultadoAnalise
from app.services.ai_service import ServicoIA
from app.services.job_analyzer import analisar_vaga
from app.services.matching_engine import calcular_compatibilidade
from app.services.resume_analyzer import analisar_curriculo
from app.services.semantic import MotorSemantico

router = APIRouter(prefix="/api/analysis", tags=["Análises"])


def _resposta(analise: Analise) -> AnaliseResposta:
    return AnaliseResposta(id=analise.id, criado_em=analise.criado_em, descricao_vaga=analise.descricao_vaga,
                           **analise.resultado)


@router.post("", response_model=AnaliseResposta, status_code=status.HTTP_201_CREATED,
             summary="Compara um currículo enviado com a descrição de uma vaga")
def criar_analise(
    dados: AnaliseRequisicao,
    db: Session = Depends(get_db),
    motor: MotorSemantico = Depends(motor_semantico),
    ia: ServicoIA = Depends(servico_ia),
):
    settings = get_settings()
    if len(dados.descricao_vaga) > settings.max_job_chars:
        raise HTTPException(422, detail={"codigo": "vaga_longa",
                                         "mensagem": f"A descrição da vaga passa de {settings.max_job_chars} caracteres."})
    curriculo = db.get(Curriculo, dados.resume_id)
    if curriculo is None:
        raise HTTPException(404, detail={"codigo": "curriculo_nao_encontrado",
                                         "mensagem": "Currículo não encontrado ou expirado. Envie o PDF novamente."})

    inicio = time.perf_counter()
    cv = analisar_curriculo(curriculo.texto, hoje=date.today())
    vaga = analisar_vaga(dados.descricao_vaga)
    matching = calcular_compatibilidade(cv, vaga, motor)
    sugestoes, fonte, aviso = ia.sugestoes(matching, cv)

    resultado = ResultadoAnalise(
        score=matching.score, classificacao=matching.classificacao, categorias=matching.categorias,
        competencias=matching.competencias, requisitos=matching.requisitos, palavras_chave=matching.palavras_chave,
        sugestoes=sugestoes, fonte_sugestoes=fonte, motor_semantico=matching.motor_semantico,
        vaga=matching.vaga, curriculo=matching.curriculo, avisos=matching.avisos + ([aviso] if aviso else []),
    )
    analise = Analise(
        curriculo_id=curriculo.id, cargo=vaga.cargo[:255], score=matching.score, classificacao=matching.classificacao,
        descricao_vaga=dados.descricao_vaga, resultado=resultado.model_dump(mode="json"),
        duracao_segundos=round(time.perf_counter() - inicio, 3),
    )
    curriculo.expira_em = None  # passa a fazer parte do histórico, até ser excluído
    db.add(analise)
    db.commit()
    return _resposta(analise)


@router.get("/history", response_model=list[HistoricoItem], summary="Lista as análises anteriores")
def listar_historico(limite: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    analises = db.scalars(select(Analise).order_by(Analise.criado_em.desc()).limit(limite)).all()
    return [HistoricoItem(id=a.id, cargo=a.cargo, score=a.score, classificacao=a.classificacao, criado_em=a.criado_em)
            for a in analises]


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT,
               summary="Exclui todo o histórico e os currículos armazenados")
def excluir_historico(db: Session = Depends(get_db)):
    db.execute(delete(Analise))
    db.execute(delete(Curriculo))
    db.commit()


@router.get("/{analysis_id}", response_model=AnaliseResposta, summary="Consulta uma análise")
def obter_analise(analysis_id: str, db: Session = Depends(get_db)):
    analise = db.get(Analise, analysis_id)
    if analise is None:
        raise HTTPException(404, detail={"codigo": "nao_encontrado", "mensagem": "Análise não encontrada."})
    return _resposta(analise)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Exclui uma análise (e o currículo, se não for usado por outra)")
def excluir_analise(analysis_id: str, db: Session = Depends(get_db)):
    analise = db.get(Analise, analysis_id)
    if analise is None:
        raise HTTPException(404, detail={"codigo": "nao_encontrado", "mensagem": "Análise não encontrada."})
    curriculo_id = analise.curriculo_id
    db.delete(analise)
    db.flush()
    restantes = db.scalar(select(func.count()).select_from(Analise).where(Analise.curriculo_id == curriculo_id))
    if not restantes:
        db.execute(delete(Curriculo).where(Curriculo.id == curriculo_id))
    db.commit()
