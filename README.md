# CV Match: Analisador Inteligente de Currículos

Aplicação web que compara um currículo em PDF com a descrição de uma vaga e mostra, de forma explicável, o quanto os dois combinam:

- **Score de compatibilidade de 0 a 100**, com a classificação (excelente, boa, moderada, baixa ou muito baixa);
- **Desempenho por critério**: competências técnicas, experiência, formação, palavras-chave, competências comportamentais, idiomas e certificações;
- **Cada requisito da vaga** marcado como atendido, parcialmente atendido ou não identificado, com a justificativa e o trecho do currículo que a sustenta;
- **Competências** separadas em encontradas, parcialmente evidenciadas e não identificadas;
- **Palavras-chave para ATS** (sistemas de triagem automática): o que já aparece, o que falta e o que está escrito de outra forma;
- **Sugestões de melhoria** e um **editor** que reescreve seções do currículo lado a lado com o original;
- **Histórico** das análises, com opção de excluir uma análise ou todos os dados.

## O problema que ele resolve

Candidatos costumam enviar o mesmo currículo para vagas diferentes sem saber quais requisitos estão bem evidenciados, quais aparecem só como uma palavra solta e quais faltam. Muitas empresas usam sistemas ATS que filtram currículos por termos exatos antes de qualquer pessoa lê-los. O CV Match mostra essas lacunas com justificativas verificáveis, para que a pessoa ajuste o currículo **sem inventar nada**.

## Decisão técnica principal: a IA não dá a nota

O score é calculado **sem IA generativa**, por regras determinísticas e similaridade semântica:

- Um catálogo de competências com sinônimos em português e inglês (`backend/app/core/catalogo.py`) reconhece tecnologias, ferramentas e competências comportamentais.
- Cada competência recebe um crédito conforme a **evidência**: usada em uma experiência ou projeto vale mais do que citada apenas numa lista; uma tecnologia equivalente (MySQL quando a vaga pede PostgreSQL) vale crédito parcial.
- Requisitos descritivos e a aderência das experiências às atividades da vaga são medidos por **similaridade semântica** (Sentence Transformers, ou TF-IDF como alternativa leve).
- Requisitos desejáveis só **aumentam** o score; nunca o reduzem.

Por isso o resultado é **reproduzível** (mesma entrada, mesmo score), **explicável** (cada ponto aponta para uma regra e um trecho) e **gratuito** (funciona sem internet e sem chave de API).

A IA generativa (Gemini, opcional, camada gratuita) só **interpreta** o resultado já calculado: escreve as sugestões de melhoria e reescreve seções no editor. Sem chave configurada, um provedor local baseado em regras faz esse papel.

O cálculo completo, com fórmulas e pesos, está em [docs/como-o-score-e-calculado.md](docs/como-o-score-e-calculado.md).

## Privacidade (LGPD)

- O PDF é lido em memória e **não é salvo**. Guardamos apenas o texto extraído.
- E-mail, telefone, CPF, CEP, data de nascimento, estado civil, gênero e endereço são **removidos antes** de qualquer análise ou armazenamento.
- A seção de contato/dados pessoais não é usada no cálculo. Idade, gênero, raça, foto e endereço **nunca** influenciam o score.
- Currículos enviados e não analisados são apagados após 24 horas (`RESUME_TTL_HOURS`).
- Excluir uma análise apaga também o texto do currículo associado; há um botão para excluir todo o histórico.
- Os logs registram apenas eventos e tipos de erro, nunca o conteúdo de currículos ou vagas.
- Para o Gemini são enviados só o resultado da análise e as seções profissionais (sem a seção de contato).

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, Recharts, Lucide React, React Router |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite |
| PDF | PyMuPDF |
| NLP | Sentence Transformers (opcional), scikit-learn (TF-IDF) |
| IA generativa (opcional) | Gemini via `google-genai`, atrás de uma camada de abstração (`ProvedorIA`) |
| Testes | pytest (backend), Vitest (frontend) |

## Arquitetura

```text
Navegador (React) ── /api ──► FastAPI
                                 ├── pdf_parser        valida o PDF e extrai o texto
                                 ├── text_utils        normalização e remoção de dados pessoais
                                 ├── resume_analyzer   seções, competências, experiência, formação, idiomas
                                 ├── job_analyzer      cargo, nível, requisitos obrigatórios/desejáveis
                                 ├── semantic          Sentence Transformers ou TF-IDF
                                 ├── matching_engine   score determinístico + justificativas
                                 ├── ai_service        sugestões e reescrita (local ou Gemini)
                                 └── SQLite            histórico de análises
```

Para trocar de provedor de IA, implemente a interface `ProvedorIA` em `backend/app/services/ai_service.py` (métodos `gerar_sugestoes` e `reescrever`) e registre-o em `obter_provedor`.

## Estrutura de diretórios

```text
cv-match/
├── backend/
│   ├── app/
│   │   ├── main.py                 aplicação FastAPI, /api/health e /api/config
│   │   ├── api/                    rotas de currículos e análises
│   │   ├── core/
│   │   │   ├── config.py           pesos, créditos, calibração e variáveis de ambiente
│   │   │   └── catalogo.py         competências, idiomas, certificações e formação
│   │   ├── database/session.py     conexão SQLite
│   │   ├── models/entities.py      tabelas (curriculos, analises)
│   │   ├── schemas/analysis.py     contrato da API (Pydantic)
│   │   └── services/               pdf_parser, resume_analyzer, job_analyzer,
│   │                               matching_engine, semantic, ai_service, text_utils
│   ├── tests/                      testes e currículos/vagas fictícios (fixtures.py)
│   ├── requirements.txt            dependências principais
│   └── requirements-semantic.txt   + Sentence Transformers (opcional)
├── frontend/
│   ├── src/
│   │   ├── components/             gráficos, listas de resultado, upload, layout
│   │   ├── pages/                  Landing, Análise, Dashboard, Editor, Histórico
│   │   ├── hooks/ services/ types/ utils/
│   ├── package.json
│   └── vite.config.ts              proxy de /api para o backend
├── docs/como-o-score-e-calculado.md
├── docker-compose.yml
└── .env.example
```

## Como executar no macOS

Você precisa do **Python 3.12+** (`python3 --version`) e do **Node.js 20.19+** (`node --version`). Se faltar algum, instale com o [Homebrew](https://brew.sh): `brew install python@3.12 node`.

### Jeito rápido: um comando só

```bash
cd cv-match
./iniciar.sh
```

O script instala as dependências na primeira vez, pede a chave do Gemini (opcional; tecle Enter para pular e usar o modo local), sobe o backend e o frontend e abre o navegador em http://localhost:5173. Para encerrar, pressione **Ctrl+C**.

A chave fica salva no arquivo `.env` e só é pedida de novo se estiver vazia. Para trocá-la, rode `./iniciar.sh --chave`.

Para abrir de qualquer pasta digitando apenas `cvmatch`, crie um atalho no seu terminal (troque o caminho pelo da sua máquina):

```bash
echo "alias cvmatch='$HOME/caminho/para/cv-match/iniciar.sh'" >> ~/.zshrc
source ~/.zshrc
```

Os passos abaixo fazem o mesmo manualmente, em dois terminais.

### 1. Backend (terminal 1)

```bash
cd cv-match/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

A API fica em http://localhost:8000 e a documentação interativa (Swagger) em http://localhost:8000/docs.

**Análise semântica completa (opcional, recomendada):** troque o `pip install` acima por

```bash
pip install -r requirements-semantic.txt
```

Isso instala o Sentence Transformers e o PyTorch (cerca de 1 GB). Na primeira análise o modelo multilíngue (~470 MB) é baixado automaticamente. As versões estão fixadas para funcionar também em Macs Intel, onde o PyTorch mais recente disponível é o 2.2.2. Sem esse passo, o CV Match usa TF-IDF e funciona normalmente, com menor capacidade de reconhecer paráfrases.

### 2. Frontend (terminal 2)

```bash
cd cv-match/frontend
npm install
npm run dev
```

Abra http://localhost:5173. O Vite encaminha as chamadas `/api` para o backend na porta 8000.

### Alternativa: Docker

Com o Docker Desktop aberto:

```bash
cd cv-match
docker compose up --build
```

Abra http://localhost:8080. Para incluir o Sentence Transformers na imagem, mude `INSTALL_SEMANTIC` para `"true"` no `docker-compose.yml`.

## Como configurar a IA opcional (Gemini)

1. Gere uma chave gratuita em https://aistudio.google.com/apikey.
2. Rode `./iniciar.sh` e cole a chave quando ela for pedida (ou `./iniciar.sh --chave` para trocar uma chave já salva).

Se preferir configurar à mão: na pasta `cv-match/`, copie o exemplo (`cp .env.example .env`), preencha `GEMINI_API_KEY=` no `.env` e reinicie o backend.

Com `AI_PROVIDER=auto` (padrão), o Gemini é usado quando há chave; se a chamada falhar (sem internet, limite da camada gratuita), o sistema volta automaticamente para o modo local e avisa no dashboard. Em qualquer caso, as reescritas passam por uma verificação que alerta quando o texto sugerido cita competências ou números que não estavam no original.

## Exemplo de uso

1. Em **Nova análise**, arraste o PDF do currículo. O sistema mostra as seções identificadas e uma prévia do texto (já sem dados de contato).
2. Cole a descrição da vaga (ou clique em **Usar vaga de exemplo**) e clique em **Analisar compatibilidade**.
3. No dashboard, veja o score, o gráfico por critério (há uma visão em tabela com pesos e pontos), os requisitos com justificativas, as competências, as palavras-chave ATS e as sugestões.
4. Clique em **Melhorar meu currículo**, escolha uma seção (ex.: Experiência), edite se quiser e clique em **Gerar sugestão**. Copie ou ajuste o resultado.

Com o currículo e a vaga fictícios de `backend/tests/fixtures.py`, uma desenvolvedora back-end Python obtém **84 (TF-IDF) a 88 (Sentence Transformers)** para uma vaga de back-end Python, e um analista de marketing obtém **28 a 29** para a mesma vaga.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/resumes/upload` | Envia o PDF (campo `arquivo`), extrai o texto e as seções |
| DELETE | `/api/resumes/{id}` | Exclui um currículo e suas análises |
| POST | `/api/resumes/improve` | Reescreve uma seção (`secao`, `texto`, `analysis_id` opcional) |
| POST | `/api/analysis` | Compara currículo e vaga (`resume_id`, `descricao_vaga`) |
| GET | `/api/analysis/history` | Lista as análises anteriores |
| DELETE | `/api/analysis/history` | Exclui todo o histórico e os currículos armazenados |
| GET | `/api/analysis/{id}` | Consulta uma análise |
| DELETE | `/api/analysis/{id}` | Exclui uma análise (e o currículo, se não for usado por outra) |
| GET | `/api/health` | Status, motor semântico e provedor de IA em uso |
| GET | `/api/config` | Pesos do score e limites de upload |

Erros de negócio voltam como `{"detail": {"codigo": "...", "mensagem": "..."}}`, por exemplo `pdf_sem_texto` (precisa de OCR), `arquivo_grande`, `formato_invalido`, `pdf_protegido`, `curriculo_nao_encontrado`.

## Testes

```bash
# Backend: 105 testes (PDFs, seções, requisitos da vaga, score, competências, IA local, API)
cd cv-match/backend
source .venv/bin/activate
pytest

# Frontend: verificação de tipos, testes e build
cd cv-match/frontend
npm run typecheck
npm test
npm run build
```

Os testes do motor de compatibilidade rodam com os dois motores semânticos (o Sentence Transformers é pulado se não estiver instalado). Os testes da API usam um banco temporário, o motor TF-IDF e a IA local, sem acessar a internet. Os PDFs de teste (inclusive um "digitalizado" sem texto e um protegido por senha) são gerados pelos próprios testes.

## Limitações conhecidas

- **PDFs digitalizados** não são lidos: o sistema identifica o caso e pede OCR, mas não faz OCR.
- **Catálogo de competências:** cobre principalmente tecnologia, dados, produto e algumas áreas de negócio. Competências fora dele só são avaliadas pela similaridade semântica, com crédito menor.
- **Seções** são identificadas por títulos comuns ("Experiência", "Formação", "Skills"…). Layouts em duas colunas ou com títulos incomuns podem misturar seções.
- **Tempo de experiência** é calculado a partir de períodos com ano (ex.: "mar/2021 – atual"); sem eles, não é calculado.
- **Calibração semântica** foi feita com poucos exemplos fictícios; deve ser revista com mais casos reais.
- **Modo local do editor** faz ajustes de forma (verbos de ação, linhas quebradas, organização de competências), não uma reescrita completa. A reescrita completa usa o Gemini.
- O provedor Gemini foi implementado e tem fallback testado, mas os testes automatizados não fazem chamadas reais à API.
- Aplicação pensada para uso individual/local: não há autenticação de usuários.

## Possíveis evoluções

- OCR para PDFs digitalizados (ex.: Tesseract).
- Catálogo de competências editável e ampliado para outras áreas (saúde, direito, engenharia).
- Calibração dos limiares com um conjunto maior de pares currículo/vaga avaliados por recrutadores.
- Exportar o diagnóstico em PDF e comparar um currículo com várias vagas.
- Contas de usuário com autenticação, se a aplicação for publicada.
