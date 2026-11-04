"""Currículos e vagas fictícios usados nos testes. Pessoas e empresas são inventadas."""

from __future__ import annotations

import pymupdf as fitz

CURRICULO_DEV_PYTHON = """Ana Exemplo Souza
Desenvolvedora Back-end
ana.exemplo@email.com | (11) 98765-4321 | São Paulo, SP
Data de nascimento: 12/03/1994

RESUMO PROFISSIONAL
Desenvolvedora back-end com foco em Python e APIs REST, experiência em times ágeis e
interesse em arquitetura de microsserviços.

EXPERIÊNCIA PROFISSIONAL
Desenvolvedora Back-end Pleno — Empresa Fictícia Pagamentos
mar/2021 – atual
• Desenvolvi APIs REST em Python com FastAPI e PostgreSQL para o sistema de cobranças.
• Implementei testes automatizados com pytest, elevando a cobertura de 40% para 85%.
• Configurei pipelines de CI/CD com GitHub Actions e conteinerizei serviços com Docker.
• Atuei em squad multidisciplinar com Scrum, apresentando entregas para stakeholders.

Desenvolvedora Júnior — Loja Exemplo Online
jan/2019 – fev/2021
• Mantive aplicações Django e consultas SQL em MySQL.
• Criei relatórios automatizados em Excel para o time financeiro.

FORMAÇÃO ACADÊMICA
Bacharelado em Ciência da Computação — Universidade Exemplo
2014 – 2018

COMPETÊNCIAS
Python, FastAPI, Django, PostgreSQL, MySQL, Docker, Git, Linux, AWS, Comunicação, Trabalho em equipe

IDIOMAS
Inglês — avançado
Espanhol — básico

CERTIFICAÇÕES
AWS Certified Cloud Practitioner (2023)
"""

CURRICULO_MARKETING = """Bruno Fictício
Analista de Marketing

RESUMO
Profissional de marketing digital com foco em campanhas de mídia paga e SEO.

EXPERIÊNCIA
Analista de Marketing — Agência Imaginária
jan/2020 – dez/2023
• Gerenciei campanhas no Google Ads com orçamento mensal de R$ 50 mil.
• Produzi relatórios de desempenho em Excel e Looker Studio.

FORMAÇÃO
Graduação em Publicidade e Propaganda — Faculdade Exemplo
2015 – 2019

IDIOMAS
Inglês intermediário
"""

VAGA_BACKEND = """Vaga: Pessoa Desenvolvedora Back-end Python Pleno

Sobre a empresa
Somos uma fintech fictícia que simplifica pagamentos para pequenos negócios.

Responsabilidades:
- Desenvolver e manter APIs REST de alta disponibilidade.
- Participar de decisões de arquitetura e revisão de código.
- Trabalhar com mensageria usando Kafka.

Requisitos:
- 3+ anos de experiência com desenvolvimento back-end.
- Experiência sólida com Python e FastAPI ou Django.
- Conhecimento em PostgreSQL.
- Experiência com Docker e Kubernetes.
- Testes automatizados.
- Boa comunicação e trabalho em equipe.
- Formação superior em Ciência da Computação ou áreas afins.
- Inglês intermediário.

Diferenciais:
- Experiência com AWS.
- Conhecimento em Terraform.
- Certificação AWS.

Benefícios
- Vale-refeição e plano de saúde.
"""

VAGA_SEM_SECOES = """Analista de Dados Júnior
Procuramos uma pessoa analista de dados para apoiar o time comercial.
É necessário conhecimento em SQL e Power BI e experiência com Python.
Inglês avançado é um diferencial.
"""


def gerar_pdf(texto: str) -> bytes:
    """Gera um PDF de texto simples (com texto selecionável) a partir de um texto."""
    documento = fitz.open()
    linhas = texto.splitlines()
    for inicio in range(0, len(linhas), 55):
        pagina = documento.new_page()
        y = 50
        for linha in linhas[inicio: inicio + 55]:
            pagina.insert_text((50, y), linha, fontname="helv", fontsize=10)
            y += 13
    conteudo = documento.tobytes()
    documento.close()
    return conteudo


def gerar_pdf_sem_texto() -> bytes:
    """Simula um currículo digitalizado: página só com um desenho, sem camada de texto."""
    documento = fitz.open()
    pagina = documento.new_page()
    pagina.draw_rect(fitz.Rect(50, 50, 300, 200), color=(0, 0, 0), fill=(0.8, 0.8, 0.8))
    conteudo = documento.tobytes()
    documento.close()
    return conteudo
