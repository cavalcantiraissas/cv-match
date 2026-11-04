// Espelha os schemas do backend (backend/app/schemas/analysis.py).

export type StatusRequisito = "atendido" | "parcial" | "nao_identificado";
export type StatusCompetencia = "encontrada" | "parcial" | "nao_identificada";
export type NivelEvidencia = "forte" | "listada" | "relacionada" | "semantica" | "ausente";
export type Prioridade = "alta" | "media" | "baixa";

export interface SecaoCurriculo {
  chave: string;
  rotulo: string;
  texto: string;
}

export interface CurriculoUpload {
  resume_id: string;
  nome_arquivo: string;
  paginas: number;
  caracteres: number;
  secoes: SecaoCurriculo[];
  previa: string;
  avisos: string[];
}

export interface CategoriaScore {
  chave: string;
  rotulo: string;
  peso: number;
  peso_efetivo: number;
  score: number | null;
  aplicavel: boolean;
  contribuicao: number;
  detalhe: string;
}

export interface CompetenciaAvaliada {
  nome: string;
  tipo: "tecnica" | "ferramenta" | "comportamental";
  obrigatoria: boolean;
  status: StatusCompetencia;
  evidencia: NivelEvidencia;
  credito: number;
  justificativa: string;
  trecho: string | null;
}

export interface RequisitoAvaliado {
  texto: string;
  categoria: string;
  obrigatorio: boolean;
  status: StatusRequisito;
  credito: number;
  justificativa: string;
  trecho: string | null;
}

export interface PalavraChave {
  termo: string;
  termo_na_vaga: string;
  obrigatoria: boolean;
  status: "presente" | "variacao" | "ausente";
  sugestao: string | null;
}

export interface Sugestao {
  titulo: string;
  descricao: string;
  prioridade: Prioridade;
  secao: string | null;
}

export interface VagaResumo {
  cargo: string;
  nivel: string | null;
  anos_experiencia: number | null;
  formacao: string | null;
  idiomas: string[];
  competencias_tecnicas: string[];
  ferramentas: string[];
  competencias_comportamentais: string[];
  certificacoes: string[];
  diferenciais: string[];
  responsabilidades: string[];
  estruturada: boolean;
}

export interface CurriculoResumo {
  secoes: SecaoCurriculo[];
  anos_experiencia: number | null;
  anos_origem: string;
  formacao: string;
  idiomas: string[];
  certificacoes: string[];
}

export interface Analise {
  id: string;
  criado_em: string;
  descricao_vaga: string;
  score: number;
  classificacao: string;
  categorias: CategoriaScore[];
  competencias: CompetenciaAvaliada[];
  requisitos: RequisitoAvaliado[];
  palavras_chave: PalavraChave[];
  sugestoes: Sugestao[];
  fonte_sugestoes: string;
  motor_semantico: string;
  vaga: VagaResumo;
  curriculo: CurriculoResumo;
  avisos: string[];
}

export interface HistoricoItem {
  id: string;
  cargo: string;
  score: number;
  classificacao: string;
  criado_em: string;
}

export interface Melhoria {
  secao: string;
  original: string;
  sugerido: string;
  observacoes: string[];
  fonte: string;
}

export interface ConfigApp {
  pesos: { chave: string; rotulo: string; peso: number }[];
  max_pdf_mb: number;
  max_pdf_paginas: number;
  max_vaga_caracteres: number;
  provedor_ia: string;
}
