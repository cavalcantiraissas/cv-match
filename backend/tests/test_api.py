from tests.fixtures import CURRICULO_DEV_PYTHON, VAGA_BACKEND, gerar_pdf, gerar_pdf_sem_texto


def _enviar(client, conteudo: bytes, nome="curriculo.pdf", tipo="application/pdf"):
    return client.post("/api/resumes/upload", files={"arquivo": (nome, conteudo, tipo)})


def _analisar(client):
    resume_id = _enviar(client, gerar_pdf(CURRICULO_DEV_PYTHON)).json()["resume_id"]
    resposta = client.post("/api/analysis", json={"resume_id": resume_id, "descricao_vaga": VAGA_BACKEND})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_health(client):
    dados = client.get("/api/health").json()
    assert dados["status"] == "ok"
    assert dados["motor_semantico"] == "tfidf"
    assert dados["provedor_ia"] == "local"


def test_config_expoe_pesos(client):
    pesos = client.get("/api/config").json()["pesos"]
    assert {p["chave"]: p["peso"] for p in pesos}["competencias_tecnicas"] == 0.30


def test_upload_extrai_secoes_e_remove_dados_pessoais(client):
    resposta = _enviar(client, gerar_pdf(CURRICULO_DEV_PYTHON))
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["paginas"] == 1
    assert "experiencia" in [s["chave"] for s in dados["secoes"]]
    assert "ana.exemplo@email.com" not in dados["previa"]
    assert "98765-4321" not in dados["previa"]
    assert "1994" not in dados["previa"]


def test_upload_rejeita_extensao_invalida(client):
    resposta = _enviar(client, b"texto", nome="curriculo.txt", tipo="text/plain")
    assert resposta.status_code == 415
    assert resposta.json()["detail"]["codigo"] == "formato_invalido"


def test_upload_rejeita_pdf_falso(client):
    resposta = _enviar(client, b"<html>nao sou pdf</html>")
    assert resposta.status_code == 422
    assert resposta.json()["detail"]["codigo"] == "formato_invalido"


def test_upload_informa_pdf_que_precisa_de_ocr(client):
    resposta = _enviar(client, gerar_pdf_sem_texto())
    assert resposta.status_code == 422
    detalhe = resposta.json()["detail"]
    assert detalhe["codigo"] == "pdf_sem_texto"
    assert "OCR" in detalhe["mensagem"]


def test_upload_rejeita_arquivo_grande(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "max_pdf_mb", 0.001)
    resposta = _enviar(client, gerar_pdf(CURRICULO_DEV_PYTHON))
    assert resposta.status_code == 413


def test_fluxo_completo_de_analise(client):
    analise = _analisar(client)
    assert 0 <= analise["score"] <= 100
    assert analise["classificacao"]
    assert len(analise["categorias"]) == 6
    assert analise["requisitos"] and analise["competencias"] and analise["palavras_chave"] and analise["sugestoes"]
    assert analise["fonte_sugestoes"] == "local"
    assert analise["vaga"]["cargo"] == "Pessoa Desenvolvedora Back-end Python Pleno"

    consultada = client.get(f"/api/analysis/{analise['id']}").json()
    assert consultada["score"] == analise["score"]
    assert consultada["requisitos"] == analise["requisitos"]

    historico = client.get("/api/analysis/history").json()
    assert historico[0]["id"] == analise["id"]
    assert historico[0]["cargo"] == analise["vaga"]["cargo"]


def test_analise_com_curriculo_inexistente(client):
    resposta = client.post("/api/analysis", json={"resume_id": "naoexiste", "descricao_vaga": VAGA_BACKEND})
    assert resposta.status_code == 404
    assert resposta.json()["detail"]["codigo"] == "curriculo_nao_encontrado"


def test_analise_exige_descricao_minima(client):
    resume_id = _enviar(client, gerar_pdf(CURRICULO_DEV_PYTHON)).json()["resume_id"]
    resposta = client.post("/api/analysis", json={"resume_id": resume_id, "descricao_vaga": "Dev Python"})
    assert resposta.status_code == 422


def test_melhorar_secao_com_contexto_da_analise(client):
    analise = _analisar(client)
    resposta = client.post("/api/resumes/improve", json={
        "secao": "experiencia", "texto": "• Responsável por desenvolver APIs em Python", "analysis_id": analise["id"],
    })
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["sugerido"] == "• Desenvolvi APIs em Python"
    assert dados["fonte"] == "local"


def test_excluir_analise_remove_o_curriculo_associado(client):
    analise = _analisar(client)
    assert client.delete(f"/api/analysis/{analise['id']}").status_code == 204
    assert client.get(f"/api/analysis/{analise['id']}").status_code == 404

    from app.database.session import SessionLocal
    from app.models.entities import Curriculo

    with SessionLocal() as db:
        assert db.query(Curriculo).filter(Curriculo.analises.any(id=analise["id"])).count() == 0


def test_excluir_todo_o_historico(client):
    _analisar(client)
    assert client.delete("/api/analysis/history").status_code == 204
    assert client.get("/api/analysis/history").json() == []

    from app.database.session import SessionLocal
    from app.models.entities import Curriculo

    with SessionLocal() as db:
        assert db.query(Curriculo).count() == 0


def test_analise_inexistente(client):
    assert client.get("/api/analysis/naoexiste").status_code == 404
    assert client.delete("/api/analysis/naoexiste").status_code == 404
