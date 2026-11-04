# Como o score é calculado

O score do CV Match é **determinístico e explicável**: a mesma entrada, com o mesmo motor semântico, sempre produz o mesmo resultado, e cada ponto pode ser rastreado até um requisito da vaga e um trecho do currículo.

A IA generativa (Gemini, opcional) **não participa do cálculo**. Ela só recebe o resultado pronto para escrever sugestões e reescrever seções.

Todos os números citados aqui ficam em [`backend/app/core/config.py`](../backend/app/core/config.py).

## Visão geral do fluxo

```text
PDF ──► pdf_parser ──► remover_dados_pessoais ──► resume_analyzer ─┐
                                                                     ├─► matching_engine ──► score + justificativas
Descrição da vaga ─────────────────────────────► job_analyzer ──────┘            │
                                                                                  ▼
                                                                   ai_service (sugestões, opcional)
```

1. **`pdf_parser`** valida o arquivo (assinatura `%PDF-`, tamanho, número de páginas, senha) e extrai a camada de texto. Se houver menos de 80 caracteres por página, o PDF é tratado como digitalizado e o usuário é orientado a usar OCR.
2. **`text_utils.remover_dados_pessoais`** apaga e-mail, telefone, CPF, CEP e linhas como "Data de nascimento", "Estado civil", "Sexo", "Endereço". O texto já sai limpo para o banco e para a análise.
3. **`resume_analyzer`** identifica as seções pelos títulos e extrai competências, tempo de experiência, formação, idiomas e certificações.
4. **`job_analyzer`** identifica cargo, nível, requisitos (obrigatórios e desejáveis), atividades e palavras-chave.
5. **`matching_engine`** compara os dois e calcula o score.

## Evidência de cada competência

Uma competência citada não vale o mesmo que uma competência usada. O crédito depende de **onde** ela aparece no currículo:

| Evidência | Crédito | Quando |
|---|---:|---|
| Uso comprovado | 100% | Aparece em Experiência, Projetos, Certificações ou Voluntariado |
| Apenas citada | 60% | Aparece só na lista de competências ou no resumo |
| Tecnologia equivalente | 40% | O currículo mostra outra tecnologia da mesma família (ex.: a vaga pede PostgreSQL, o currículo tem MySQL) |
| Trecho relacionado | 40% | Requisito descritivo sem termo do catálogo, mas com uma frase do currículo semanticamente próxima |
| Não encontrada | 0% | — |

Algumas competências comprovam outras (`implica` no catálogo): usar PostgreSQL comprova SQL; usar Scrum comprova metodologias ágeis.

A seção de contato/informações pessoais nunca conta como evidência.

## Obrigatórios x desejáveis

Regras, em ordem de prioridade:

1. Palavras na própria linha: "desejável", "diferencial", "nice to have", "plus" → desejável; "obrigatório", "imprescindível", "essencial" → obrigatório.
2. A seção da vaga: "Requisitos/Qualificações" → obrigatório; "Diferenciais/Desejável" → desejável.
3. Tecnologias citadas só em "Responsabilidades/Atividades" → desejáveis (a vaga as menciona, mas não as exige).
4. Vagas sem seções → itens com cara de requisito são tratados como obrigatórios (e o dashboard avisa).

**Desejáveis nunca reduzem o score.** Dentro de cada categoria:

```text
score = (Σ créditos obrigatórios + 0,5 × Σ créditos desejáveis) / (nº obrigatórios + 0,5 × Σ créditos desejáveis)
```

O crédito do desejável entra no numerador e no denominador ao mesmo tempo: um diferencial atendido puxa o score para cima; um não atendido não muda nada. Uma categoria sem nenhum requisito obrigatório fica fora do cálculo.

## Categorias e pesos

| Categoria | Peso | O que mede |
|---|---:|---|
| Competências técnicas | 30% | Crédito de evidência de cada tecnologia/ferramenta pedida |
| Experiência profissional | 25% | 60% tempo de experiência (calculado pelos períodos do currículo) + 40% aderência das experiências às atividades da vaga (similaridade semântica). Requisitos descritivos sem termo do catálogo entram aqui com 25% |
| Formação acadêmica | 15% | Nível (médio < técnico < graduação < pós < mestrado < doutorado), conclusão e área ("áreas afins" aceita grupos próximos) |
| Palavras-chave e tecnologias | 15% | Presença **literal** do termo da vaga no currículo, como um ATS faria. Mesma competência com outra grafia ("Postgres" x "PostgreSQL") vale 75% |
| Competências comportamentais | 10% | Mesmo critério de evidência das técnicas |
| Idiomas e certificações | 5% | Nível do idioma comparado ao exigido; certificações reconhecidas pelo catálogo |

Quando a vaga não tem requisitos obrigatórios de uma categoria, ela sai do cálculo e os pesos restantes são redistribuídos proporcionalmente. O dashboard mostra o peso efetivo e quantos pontos cada categoria somou.

Quando a vaga não informa os anos de experiência, usamos uma estimativa a partir do nível do cargo (Júnior 1, Pleno 3, Sênior 5 anos), sinalizada como "(estimativa)" na justificativa.

## Status dos requisitos

| Crédito | Status |
|---|---|
| ≥ 75% | Atendido |
| 30% a 74% | Parcialmente atendido |
| < 30% | Não identificado |

## Similaridade semântica

Dois motores com a mesma interface (`services/semantic.py`):

- **Sentence Transformers** (`paraphrase-multilingual-MiniLM-L12-v2`): entende paráfrases em português e inglês. Usado quando instalado.
- **TF-IDF de n-gramas de caracteres** (scikit-learn): leve, sem download; capta variações de escrita, mas não paráfrases.

O cosseno bruto é convertido para 0–1 com uma faixa calibrada por motor (`CALIBRACAO_SEMANTICA`), medida com os casos de `backend/tests/fixtures.py`. O motor usado fica registrado em cada análise. Os testes do motor de compatibilidade rodam com os dois.

## Por que não deixar a IA dar a nota

- **Reprodutibilidade:** um LLM pode dar notas diferentes para a mesma entrada.
- **Explicabilidade:** cada ponto aqui tem uma regra e um trecho de origem.
- **Custo e privacidade:** a análise funciona sem rede e sem enviar o currículo para terceiros.
- **Viés:** características pessoais são removidas antes; não há como o modelo considerá-las.

## Limitações conhecidas

- O catálogo de competências cobre principalmente tecnologia, dados, produto e algumas áreas de negócio. Termos fora dele só são avaliados pela similaridade semântica (crédito menor).
- A identificação de seções depende de títulos reconhecíveis ("Experiência", "Skills" etc.).
- Os anos de experiência são somados a partir de períodos com ano (ex.: "mar/2021 – atual"); sem períodos, o tempo não é calculado.
- A calibração semântica foi feita com poucos exemplos e deve ser revista com mais casos reais.
