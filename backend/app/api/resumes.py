"""Rotas de currículo: upload, exclusão e editor de seções."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.deps import servico_ia
from app.core.config import get_settings
from app.database.session import get_db
from app.models.entities import Analise, Curriculo
from app.schemas.analysis import CurriculoUploadResposta, MelhoriaRequisicao, MelhoriaResposta, SecaoCurriculo
from app.services.ai_service import ServicoIA, contexto_vaga
from app.services.pdf_parser import ErroPDF, extrair_texto_pdf
from app.services.resume_analyzer import identificar_secoes
from app.services.text_utils import remover_dados_pessoais

router = APIRouter(prefix="/api/resumes", tags=["Currículos"])

TIPOS_ACEITOS = {"application/pdf", "application/x-pdf", "application/octet-stream", ""}


def limpar_expirados(db: Session) -> None:
    """Apaga currículos enviados e nunca analisados após o prazo configurado."""
    db.execute(delete(Curriculo).where(Curriculo.expira_em.is_not(None), Curriculo.expira_em < datetime.now(timezone.utc)))
    db.commit()


@router.post("/upload", response_model=CurriculoUploadResposta, status_code=status.HTTP_201_CREATED,
             summary="Envia um currículo em PDF e extrai o texto")
async def enviar_curriculo(arquivo: UploadFile = File(..., description="Currículo em PDF"), db: Session = Depends(get_db)):
    settings = get_settings()
    nome = (arquivo.filename or "curriculo.pdf").rsplit("/", 1)[-1][:255]
    if not nome.lower().endswith(".pdf") or (arquivo.content_type or "") not in TIPOS_ACEITOS:
        raise HTTPException(415, detail={"codigo": "formato_invalido", "mensagem": "Envie o currículo em formato PDF."})

    # Lê no máximo o limite + 1 byte, para não carregar arquivos enormes na memória.
    conteudo = await arquivo.read(settings.max_pdf_bytes + 1)
    try:
        pdf = extrair_texto_pdf(conteudo, settings.max_pdf_bytes, settings.max_pdf_pages)
    except ErroPDF as erro:
        codigo_http = 413 if erro.codigo == "arquivo_grande" else 422
        raise HTTPException(codigo_http, detail={"codigo": erro.codigo, "mensagem": erro.mensagem})

    texto = remover_dados_pessoais(pdf.texto)
    secoes = identificar_secoes(texto)

    limpar_expirados(db)
    curriculo = Curriculo(
        nome_arquivo=nome, paginas=pdf.paginas, texto=texto,
        expira_em=datetime.now(timezone.utc) + timedelta(hours=settings.resume_ttl_hours),
    )
    db.add(curriculo)
    db.commit()

    avisos = []
    reconhecidas = [s for s in secoes if s.chave not in ("informacoes", "geral")]
    if len(reconhecidas) < 2:
        avisos.append("Identificamos poucas seções no currículo. Títulos como “Experiência”, “Formação” e "
                      "“Competências” ajudam a análise e os sistemas ATS.")
    if pdf.paginas > 3:
        avisos.append(f"O currículo tem {pdf.paginas} páginas. Para a maioria das vagas, 1 a 2 páginas são suficientes.")

    return CurriculoUploadResposta(
        resume_id=curriculo.id, nome_arquivo=nome, paginas=pdf.paginas, caracteres=len(texto),
        secoes=[SecaoCurriculo(chave=s.chave, rotulo=s.rotulo, texto=s.texto) for s in secoes],
        previa=texto[:1500], avisos=avisos,
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Exclui um currículo e suas análises")
def excluir_curriculo(resume_id: str, db: Session = Depends(get_db)):
    curriculo = db.get(Curriculo, resume_id)
    if curriculo is None:
        raise HTTPException(404, detail={"codigo": "nao_encontrado", "mensagem": "Currículo não encontrado."})
    db.delete(curriculo)
    db.commit()


@router.post("/improve", response_model=MelhoriaResposta, summary="Sugere uma versão reescrita de uma seção")
def melhorar_secao(dados: MelhoriaRequisicao, db: Session = Depends(get_db), ia: ServicoIA = Depends(servico_ia)):
    vaga = None
    if dados.analysis_id:
        analise = db.get(Analise, dados.analysis_id)
        if analise is None:
            raise HTTPException(404, detail={"codigo": "nao_encontrado", "mensagem": "Análise não encontrada."})
        vaga = contexto_vaga(analise.resultado)
    reescrita, fonte = ia.reescrever(dados.secao, dados.texto, vaga)
    return MelhoriaResposta(secao=dados.secao, original=dados.texto, sugerido=reescrita.texto,
                            observacoes=reescrita.observacoes, fonte=fonte)
