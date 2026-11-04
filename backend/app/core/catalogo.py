"""
Catálogo de competências, idiomas, certificações e formação.

É a base determinística do motor: um termo só é reconhecido como competência se
estiver aqui (ou for capturado pela análise semântica, que tem crédito menor).

Convenções dos sinônimos:
- comparados em texto minúsculo e sem acentos;
- prefixo "=" indica sinônimo sensível a maiúsculas (ex.: "=Go", "=R"), para
  evitar falsos positivos com palavras comuns.

`familia` agrupa tecnologias equivalentes: se a vaga pede PostgreSQL e o
currículo mostra MySQL, a competência é considerada "relacionada" (crédito parcial).
`implica` lista competências comprovadas pelo uso desta (PostgreSQL -> SQL).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Competencia:
    nome: str
    tipo: str  # "tecnica" | "ferramenta" | "comportamental"
    grupo: str  # rótulo usado para organizar a seção de competências
    sinonimos: tuple[str, ...]
    familia: str | None = None
    implica: tuple[str, ...] = field(default_factory=tuple)


def _c(nome, tipo, grupo, sinonimos, familia=None, implica=()):
    return Competencia(nome, tipo, grupo, tuple(sinonimos), familia, tuple(implica))


LING = "Linguagens"
FW = "Frameworks e bibliotecas"
DADOS = "Dados e bancos de dados"
CLOUD = "Cloud e DevOps"
IA = "Dados, IA e analytics"
PRAT = "Práticas e metodologias"
FERR = "Ferramentas"
NEG = "Negócios e gestão"
COMP = "Competências comportamentais"

COMPETENCIAS: list[Competencia] = [
    # Linguagens
    _c("Python", "tecnica", LING, ["python", "python3"]),
    _c("JavaScript", "tecnica", LING, ["javascript", "=JS", "ecmascript", "es6"]),
    _c("TypeScript", "tecnica", LING, ["typescript", "=TS"], implica=["JavaScript"]),
    _c("Java", "tecnica", LING, ["java"], familia="jvm"),
    _c("Kotlin", "tecnica", LING, ["kotlin"], familia="jvm"),
    _c("C#", "tecnica", LING, ["c#", "csharp", "c sharp"]),
    _c("C++", "tecnica", LING, ["c++", "cpp"]),
    _c("C", "tecnica", LING, ["linguagem c", "c language", "=C/C++"]),
    _c("Go", "tecnica", LING, ["golang", "=Go", "linguagem go"]),
    _c("Rust", "tecnica", LING, ["rust"]),
    _c("PHP", "tecnica", LING, ["php"]),
    _c("Ruby", "tecnica", LING, ["ruby"]),
    _c("Swift", "tecnica", LING, ["swift"]),
    _c("Dart", "tecnica", LING, ["dart"]),
    _c("R", "tecnica", LING, ["linguagem r", "r language", "rstudio", "=R,", "=R e", "=R ("]),
    _c("SQL", "tecnica", DADOS, ["sql", "t-sql", "pl/sql", "plsql"]),
    _c("HTML", "tecnica", LING, ["html", "html5"]),
    _c("CSS", "tecnica", LING, ["css", "css3", "sass", "scss"]),
    _c("Shell Script", "tecnica", LING, ["shell script", "bash", "shell"]),
    _c("Scala", "tecnica", LING, ["scala"], familia="jvm"),
    # Frameworks e bibliotecas
    _c("React", "tecnica", FW, ["react", "react.js", "reactjs"], "frontend_fw", ["JavaScript"]),
    _c("Next.js", "tecnica", FW, ["next.js", "nextjs"], "frontend_fw", ["React"]),
    _c("Vue.js", "tecnica", FW, ["vue", "vue.js", "vuejs", "nuxt"], "frontend_fw", ["JavaScript"]),
    _c("Angular", "tecnica", FW, ["angular", "angularjs"], "frontend_fw", ["TypeScript"]),
    _c("Svelte", "tecnica", FW, ["svelte", "sveltekit"], "frontend_fw"),
    _c("React Native", "tecnica", FW, ["react native"], "mobile", ["React"]),
    _c("Flutter", "tecnica", FW, ["flutter"], "mobile", ["Dart"]),
    _c("Node.js", "tecnica", FW, ["node.js", "nodejs", "node"], "backend_js", ["JavaScript"]),
    _c("Express", "tecnica", FW, ["express", "express.js"], "backend_js", ["Node.js"]),
    _c("NestJS", "tecnica", FW, ["nestjs", "nest.js"], "backend_js", ["Node.js", "TypeScript"]),
    _c("Django", "tecnica", FW, ["django"], "backend_py", ["Python"]),
    _c("Flask", "tecnica", FW, ["flask"], "backend_py", ["Python"]),
    _c("FastAPI", "tecnica", FW, ["fastapi"], "backend_py", ["Python"]),
    _c("Spring", "tecnica", FW, ["spring", "spring boot", "springboot"], "backend_jvm", ["Java"]),
    _c(".NET", "tecnica", FW, [".net", "dotnet", "asp.net", ".net core"], "backend_ms", ["C#"]),
    _c("Laravel", "tecnica", FW, ["laravel"], "backend_php", ["PHP"]),
    _c("Ruby on Rails", "tecnica", FW, ["rails", "ruby on rails"], None, ["Ruby"]),
    _c("Tailwind CSS", "tecnica", FW, ["tailwind", "tailwindcss"], "css_fw", ["CSS"]),
    _c("Bootstrap", "tecnica", FW, ["bootstrap"], "css_fw", ["CSS"]),
    _c("Pandas", "tecnica", IA, ["pandas"], "dados_py", ["Python"]),
    _c("NumPy", "tecnica", IA, ["numpy"], "dados_py", ["Python"]),
    _c("Scikit-learn", "tecnica", IA, ["scikit-learn", "sklearn", "scikit learn"], "ml_lib", ["Machine Learning", "Python"]),
    _c("TensorFlow", "tecnica", IA, ["tensorflow", "keras"], "dl_lib", ["Deep Learning"]),
    _c("PyTorch", "tecnica", IA, ["pytorch", "torch"], "dl_lib", ["Deep Learning"]),
    _c("Spark", "tecnica", IA, ["spark", "pyspark", "apache spark"], "big_data"),
    _c("Airflow", "ferramenta", IA, ["airflow", "apache airflow"], "orquestracao_dados"),
    _c("dbt", "ferramenta", IA, ["=dbt", "data build tool"], "orquestracao_dados", ["SQL"]),
    _c("GraphQL", "tecnica", FW, ["graphql"], "api"),
    _c("REST", "tecnica", PRAT, ["rest", "restful", "api rest", "apis rest", "rest api"], "api"),
    _c("Microsserviços", "tecnica", PRAT, ["microsservicos", "microservicos", "microservices", "micro-servicos"]),
    # Bancos de dados
    _c("PostgreSQL", "ferramenta", DADOS, ["postgresql", "postgres"], "sql_db", ["SQL"]),
    _c("MySQL", "ferramenta", DADOS, ["mysql", "mariadb"], "sql_db", ["SQL"]),
    _c("SQL Server", "ferramenta", DADOS, ["sql server", "sqlserver", "mssql"], "sql_db", ["SQL"]),
    _c("Oracle Database", "ferramenta", DADOS, ["oracle database", "oracle db", "banco oracle", "oracle"], "sql_db", ["SQL"]),
    _c("SQLite", "ferramenta", DADOS, ["sqlite"], "sql_db", ["SQL"]),
    _c("MongoDB", "ferramenta", DADOS, ["mongodb", "mongo"], "nosql_db"),
    _c("Redis", "ferramenta", DADOS, ["redis"], "cache"),
    _c("DynamoDB", "ferramenta", DADOS, ["dynamodb"], "nosql_db"),
    _c("Elasticsearch", "ferramenta", DADOS, ["elasticsearch", "elastic search", "opensearch"]),
    _c("BigQuery", "ferramenta", DADOS, ["bigquery", "big query"], "data_warehouse", ["SQL"]),
    _c("Snowflake", "ferramenta", DADOS, ["snowflake"], "data_warehouse", ["SQL"]),
    _c("Kafka", "ferramenta", CLOUD, ["kafka", "apache kafka"], "mensageria"),
    _c("RabbitMQ", "ferramenta", CLOUD, ["rabbitmq", "rabbit mq"], "mensageria"),
    # Cloud e DevOps
    _c("AWS", "ferramenta", CLOUD, ["aws", "amazon web services", "ec2", "lambda", "s3"], "cloud"),
    _c("Azure", "ferramenta", CLOUD, ["azure", "microsoft azure"], "cloud"),
    _c("Google Cloud", "ferramenta", CLOUD, ["google cloud", "gcp", "google cloud platform"], "cloud"),
    _c("Docker", "ferramenta", CLOUD, ["docker", "containers", "conteineres", "docker compose"], "containers"),
    _c("Kubernetes", "ferramenta", CLOUD, ["kubernetes", "k8s", "eks", "aks", "gke", "openshift"], "orquestracao", ["Docker"]),
    _c("Terraform", "ferramenta", CLOUD, ["terraform", "infraestrutura como codigo", "infrastructure as code", "iac"], "iac"),
    _c("CI/CD", "tecnica", CLOUD, ["ci/cd", "ci cd", "integracao continua", "entrega continua", "continuous integration", "pipelines"], "ci_cd"),
    _c("GitHub Actions", "ferramenta", CLOUD, ["github actions"], "ci_cd", ["CI/CD"]),
    _c("Jenkins", "ferramenta", CLOUD, ["jenkins"], "ci_cd", ["CI/CD"]),
    _c("GitLab CI", "ferramenta", CLOUD, ["gitlab ci", "gitlab-ci"], "ci_cd", ["CI/CD"]),
    _c("Linux", "ferramenta", CLOUD, ["linux", "ubuntu", "debian", "unix"]),
    _c("Git", "ferramenta", FERR, ["git", "github", "gitlab", "bitbucket", "versionamento"]),
    _c("Observabilidade", "tecnica", CLOUD, ["observabilidade", "observability", "monitoramento", "prometheus", "grafana", "datadog", "new relic"]),
    # Dados, IA e analytics
    _c("Machine Learning", "tecnica", IA, ["machine learning", "aprendizado de maquina", "=ML", "modelos preditivos"], "ml"),
    _c("Deep Learning", "tecnica", IA, ["deep learning", "redes neurais", "neural networks"], "ml", ["Machine Learning"]),
    _c("NLP", "tecnica", IA, ["nlp", "processamento de linguagem natural", "natural language processing"], "ml", ["Machine Learning"]),
    _c("IA Generativa", "tecnica", IA, ["llm", "llms", "ia generativa", "generative ai", "genai", "rag", "engenharia de prompt", "prompt engineering"], "ml"),
    _c("Estatística", "tecnica", IA, ["estatistica", "statistics", "estatistico", "teste a/b", "testes a/b", "a/b testing"]),
    _c("ETL", "tecnica", IA, ["etl", "elt", "pipeline de dados", "pipelines de dados", "data pipeline", "engenharia de dados"]),
    _c("Power BI", "ferramenta", IA, ["power bi", "powerbi", "dax"], "bi"),
    _c("Tableau", "ferramenta", IA, ["tableau"], "bi"),
    _c("Looker", "ferramenta", IA, ["looker", "looker studio", "data studio"], "bi"),
    _c("Excel", "ferramenta", FERR, ["excel", "planilhas", "spreadsheets", "vba", "google sheets"]),
    # Práticas
    _c("Testes automatizados", "tecnica", PRAT, ["testes automatizados", "testes unitarios", "testes de integracao", "unit tests", "automated tests", "tdd", "pytest", "jest", "vitest", "junit", "cypress", "selenium", "playwright"]),
    _c("Clean Code", "tecnica", PRAT, ["clean code", "codigo limpo", "solid", "design patterns", "padroes de projeto", "clean architecture", "arquitetura limpa"]),
    _c("Scrum", "tecnica", PRAT, ["scrum", "sprint", "sprints"], "agil", ["Metodologias ágeis"]),
    _c("Kanban", "tecnica", PRAT, ["kanban"], "agil", ["Metodologias ágeis"]),
    _c("Metodologias ágeis", "tecnica", PRAT, ["metodologias ageis", "metodologia agil", "agile", "agil", "safe"], "agil"),
    _c("UX/UI Design", "tecnica", PRAT, ["ux", "ui", "ux/ui", "ui/ux", "user experience", "experiencia do usuario", "design de interface"]),
    _c("Segurança da informação", "tecnica", PRAT, ["seguranca da informacao", "information security", "ciberseguranca", "cybersecurity", "owasp", "appsec"]),
    _c("LGPD", "tecnica", NEG, ["lgpd", "gdpr", "lei geral de protecao de dados", "protecao de dados"]),
    _c("Gestão de projetos", "tecnica", NEG, ["gestao de projetos", "gerenciamento de projetos", "project management", "pmbok"]),
    _c("Gestão de produto", "tecnica", NEG, ["gestao de produto", "product management", "product owner", "roadmap de produto", "discovery"]),
    _c("Análise de dados", "tecnica", IA, ["analise de dados", "data analysis", "analytics", "analista de dados"]),
    _c("Marketing digital", "tecnica", NEG, ["marketing digital", "seo", "sem", "google ads", "inbound", "growth"]),
    _c("Vendas", "tecnica", NEG, ["vendas", "sales", "prospeccao", "pipeline comercial", "negociacao comercial"]),
    _c("Atendimento ao cliente", "tecnica", NEG, ["atendimento ao cliente", "customer success", "customer service", "suporte ao cliente", "sucesso do cliente"]),
    _c("Finanças", "tecnica", NEG, ["financas", "fluxo de caixa", "contabilidade", "controladoria", "fp&a", "planejamento financeiro"]),
    _c("Recrutamento e seleção", "tecnica", NEG, ["recrutamento", "selecao de pessoas", "recruitment", "talent acquisition", "r&s"]),
    # Ferramentas
    _c("Jira", "ferramenta", FERR, ["jira", "confluence"], "gestao_tarefas"),
    _c("Trello", "ferramenta", FERR, ["trello", "asana", "monday", "clickup"], "gestao_tarefas"),
    _c("Figma", "ferramenta", FERR, ["figma"], "design_tool"),
    _c("Adobe XD", "ferramenta", FERR, ["adobe xd", "sketch"], "design_tool"),
    _c("Photoshop", "ferramenta", FERR, ["photoshop", "illustrator", "adobe creative"], "design_grafico"),
    _c("SAP", "ferramenta", FERR, ["sap", "s/4hana", "sap hana"], "erp"),
    _c("Salesforce", "ferramenta", FERR, ["salesforce"], "crm"),
    _c("HubSpot", "ferramenta", FERR, ["hubspot"], "crm"),
    _c("Postman", "ferramenta", FERR, ["postman", "insomnia"], "api_tool"),
    # Competências comportamentais
    _c("Comunicação", "comportamental", COMP, ["comunicacao", "comunicativo", "comunicativa", "communication", "apresentei", "apresentacoes", "oratoria"]),
    _c("Trabalho em equipe", "comportamental", COMP, ["trabalho em equipe", "colaboracao", "colaborativo", "colaborativa", "teamwork", "collaboration", "equipes multidisciplinares", "times multidisciplinares", "squad"]),
    _c("Liderança", "comportamental", COMP, ["lideranca", "liderei", "lideranca tecnica", "leadership", "gestao de equipe", "gestao de pessoas", "coordenei", "lider tecnico", "tech lead"]),
    _c("Resolução de problemas", "comportamental", COMP, ["resolucao de problemas", "solucao de problemas", "problem solving", "resolvi", "solucionei"]),
    _c("Proatividade", "comportamental", COMP, ["proatividade", "proativo", "proativa", "iniciativa", "proactive"]),
    _c("Pensamento analítico", "comportamental", COMP, ["pensamento analitico", "analitico", "analitica", "analytical", "raciocinio logico", "pensamento critico", "critical thinking"]),
    _c("Organização", "comportamental", COMP, ["organizacao", "organizado", "organizada", "gestao do tempo", "time management", "planejamento"]),
    _c("Adaptabilidade", "comportamental", COMP, ["adaptabilidade", "flexibilidade", "adaptability", "resiliencia", "resilience"]),
    _c("Autonomia", "comportamental", COMP, ["autonomia", "autonomo", "autonoma", "autonomy", "independente"]),
    _c("Negociação", "comportamental", COMP, ["negociacao", "negociei", "negotiation"]),
    _c("Criatividade", "comportamental", COMP, ["criatividade", "criativo", "criativa", "creativity", "inovacao"]),
    _c("Empatia", "comportamental", COMP, ["empatia", "empatico", "empatica", "empathy", "escuta ativa"]),
    _c("Mentoria", "comportamental", COMP, ["mentoria", "mentorei", "mentoring", "mentor", "treinei", "onboarding de novos"]),
    _c("Orientação a resultados", "comportamental", COMP, ["orientacao a resultados", "foco em resultados", "results-oriented", "orientado a resultados", "orientada a resultados", "metas"]),
    _c("Aprendizado contínuo", "comportamental", COMP, ["aprendizado continuo", "vontade de aprender", "continuous learning", "curiosidade", "autodidata"]),
    _c("Visão de negócio", "comportamental", COMP, ["visao de negocio", "business acumen", "visao estrategica", "pensamento estrategico"]),
    _c("Atenção aos detalhes", "comportamental", COMP, ["atencao aos detalhes", "atencao a detalhes", "detalhista", "attention to detail"]),
    _c("Relacionamento com stakeholders", "comportamental", COMP, ["stakeholders", "relacionamento interpessoal", "relacionamento com clientes", "interpessoal"]),
]

COMPETENCIA_POR_NOME: dict[str, Competencia] = {c.nome: c for c in COMPETENCIAS}

# Idiomas: nome -> sinônimos (sem acento, minúsculos)
IDIOMAS: dict[str, tuple[str, ...]] = {
    "Inglês": ("ingles", "english"),
    "Espanhol": ("espanhol", "spanish", "espanol"),
    "Francês": ("frances", "french"),
    "Alemão": ("alemao", "german"),
    "Italiano": ("italiano", "italian"),
    "Japonês": ("japones", "japanese"),
    "Mandarim": ("mandarim", "chines", "mandarin", "chinese"),
    "Português": ("portugues", "portuguese"),
}

# Níveis de idioma: padrão -> nível numérico (1 a 5). A ordem importa: os mais
# específicos primeiro.
NIVEIS_IDIOMA: list[tuple[str, int, str]] = [
    (r"nativ|native|lingua materna|mother tongue", 5, "Nativo"),
    (r"fluente|fluencia|fluent|fluency|proficien|\bc2\b", 4, "Fluente"),
    (r"avancad|advanced|upper[- ]intermediate|\bc1\b", 3, "Avançado"),
    (r"intermediari|intermediate|conversacao|conversational|\bb1\b|\bb2\b", 2, "Intermediário"),
    (r"tecnico|technical|leitura|reading", 2, "Intermediário (técnico/leitura)"),
    (r"basic|elementar|elementary|\ba1\b|\ba2\b", 1, "Básico"),
]
ROTULO_NIVEL_IDIOMA = {1: "Básico", 2: "Intermediário", 3: "Avançado", 4: "Fluente", 5: "Nativo"}

# Certificações reconhecidas: nome -> padrões regex (sem acento, minúsculos)
CERTIFICACOES: dict[str, tuple[str, ...]] = {
    "AWS Certified": (r"aws certified", r"certifica\w* aws", r"aws (solutions architect|developer|cloud practitioner|sysops)"),
    "Microsoft Azure (AZ/DP/AI)": (r"\baz-\d{3}\b", r"\bdp-\d{3}\b", r"\bai-\d{3}\b", r"azure (fundamentals|administrator|developer|solutions architect)"),
    "Google Cloud Certified": (r"google cloud certified", r"certifica\w* (gcp|google cloud)", r"professional cloud architect"),
    "Kubernetes (CKA/CKAD)": (r"\bcka\b", r"\bckad\b", r"certified kubernetes"),
    "Scrum (CSM/PSM)": (r"\bcsm\b", r"\bpsm( i{1,3})?\b", r"scrum master certifi", r"certified scrum", r"professional scrum"),
    "PMP": (r"\bpmp\b", r"project management professional"),
    "ITIL": (r"\bitil\b",),
    "ISTQB": (r"\bistqb\b", r"\bctfl\b"),
    "CCNA": (r"\bccna\b", r"\bccnp\b"),
    "CompTIA": (r"comptia", r"security\+"),
    "Six Sigma": (r"six sigma", r"lean six sigma", r"green belt", r"black belt"),
    "Certificações financeiras (CPA/CEA/CFA)": (r"\bcpa[- ]?(10|20)\b", r"\bcea\b", r"\bcfa\b", r"\bcfp\b"),
    "Oracle Certified": (r"oracle certified", r"\bocp\b", r"\boca\b"),
    "Exame de proficiência em idioma": (r"\btoefl\b", r"\bielts\b", r"\btoeic\b", r"cambridge (fce|cae|cpe|english)", r"\bdele\b"),
}

# Formação: padrão -> nível (ordem do mais alto para o mais baixo)
NIVEIS_FORMACAO: list[tuple[str, int, str]] = [
    (r"doutorad|ph\.?d|doctorate", 6, "Doutorado"),
    (r"mestrad|mestre em|master'?s|\bmsc\b|m\.sc", 5, "Mestrado"),
    (r"pos[- ]graduac|especializac|\bmba\b|lato sensu|postgraduate", 4, "Pós-graduação"),
    (r"graduac|bacharel|licenciatura|tecnologo|ensino superior|nivel superior|superior completo|superior em|faculdade|universidade|bachelor|\bb\.?sc\b|degree|engenharia", 3, "Graduação"),
    (r"curso tecnico|tecnico em|ensino tecnico|tecnico de nivel medio", 2, "Técnico"),
    (r"ensino medio|segundo grau|high school", 1, "Ensino médio"),
]

# Áreas de formação e o grupo a que pertencem (para "áreas afins").
AREAS_FORMACAO: dict[str, tuple[str, tuple[str, ...]]] = {
    "Ciência da Computação": ("tecnologia", ("ciencia da computacao", "computer science", "computacao")),
    "Sistemas de Informação": ("tecnologia", ("sistemas de informacao", "information systems")),
    "Engenharia de Software": ("tecnologia", ("engenharia de software", "software engineering")),
    "Análise e Desenvolvimento de Sistemas": ("tecnologia", ("analise e desenvolvimento de sistemas", "ads")),
    "Engenharia da Computação": ("tecnologia", ("engenharia da computacao", "engenharia de computacao", "computer engineering")),
    "Tecnologia da Informação": ("tecnologia", ("tecnologia da informacao", "information technology", "redes de computadores", "ciencia de dados", "data science", "inteligencia artificial")),
    "Engenharia": ("engenharia", ("engenharia eletrica", "engenharia de producao", "engenharia mecanica", "engenharia civil", "engenharia quimica", "engenharia", "engineering")),
    "Matemática e Estatística": ("exatas", ("matematica", "estatistica", "mathematics", "statistics", "fisica", "physics", "atuaria")),
    "Administração": ("negocios", ("administracao", "business administration", "gestao")),
    "Economia": ("negocios", ("economia", "economics", "ciencias economicas")),
    "Contabilidade": ("negocios", ("contabeis", "ciencias contabeis", "contabilidade", "accounting")),
    "Marketing e Comunicação": ("comunicacao", ("marketing", "publicidade", "comunicacao social", "jornalismo", "relacoes publicas")),
    "Design": ("comunicacao", ("design", "desenho industrial", "design grafico")),
    "Direito": ("direito", ("direito", "law")),
    "Psicologia": ("humanas", ("psicologia", "psychology")),
    "Recursos Humanos": ("humanas", ("recursos humanos", "gestao de pessoas", "human resources")),
}
# Grupos considerados próximos entre si quando a vaga aceita "áreas afins".
GRUPOS_PROXIMOS: dict[str, set[str]] = {
    "tecnologia": {"engenharia", "exatas"},
    "engenharia": {"tecnologia", "exatas"},
    "exatas": {"tecnologia", "engenharia", "negocios"},
    "negocios": {"exatas"},
}

NIVEIS_SENIORIDADE: list[tuple[str, str, int]] = [
    # padrão, rótulo, anos de experiência tipicamente esperados
    (r"estagi|\bintern\b|internship|trainee", "Estágio/Trainee", 0),
    (r"junior|\bjr\.?\b|entry[- ]level", "Júnior", 1),
    (r"pleno|\bmid[- ]level\b|\bmid\b|\bpl\b", "Pleno", 3),
    (r"senior|\bsr\.?\b", "Sênior", 5),
    (r"especialista|specialist|staff|principal", "Especialista", 7),
    (r"\blead\b|lider|\bhead\b|gerente|manager|coordenador", "Liderança", 6),
]
