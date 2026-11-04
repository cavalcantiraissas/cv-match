import type { NivelEvidencia, Prioridade } from "../types/api";

export type Faixa = "good" | "warning" | "serious" | "critical";

/** Faixa de status do score (mesmos limites da classificação do backend). */
export function faixaDoScore(score: number): Faixa {
  if (score >= 75) return "good";
  if (score >= 60) return "warning";
  if (score >= 40) return "serious";
  return "critical";
}

export const COR_FAIXA: Record<Faixa, { traco: string; trilha: string }> = {
  good: { traco: "#0ca30c", trilha: "#dcf3dc" },
  warning: { traco: "#fab219", trilha: "#fdf0cf" },
  serious: { traco: "#ec835a", trilha: "#fbe4da" },
  critical: { traco: "#d03b3b", trilha: "#f6dcdc" },
};

export function formatarData(iso: string): string {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
}

export function formatarPercentual(valor: number, casas = 0): string {
  return `${valor.toLocaleString("pt-BR", { maximumFractionDigits: casas, minimumFractionDigits: casas })}%`;
}

export function formatarTamanho(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MB`;
}

export const ROTULO_EVIDENCIA: Record<NivelEvidencia, string> = {
  forte: "Uso comprovado",
  listada: "Apenas citada",
  relacionada: "Tecnologia equivalente",
  semantica: "Trecho relacionado",
  ausente: "Não encontrada",
};

export const ROTULO_PRIORIDADE: Record<Prioridade, string> = { alta: "Alta", media: "Média", baixa: "Baixa" };

export const ROTULO_MOTOR: Record<string, string> = {
  "sentence-transformers": "Sentence Transformers (semântico)",
  tfidf: "TF-IDF (léxico)",
};

export const ROTULO_FONTE: Record<string, string> = { local: "Modo local (regras)", gemini: "Gemini" };
