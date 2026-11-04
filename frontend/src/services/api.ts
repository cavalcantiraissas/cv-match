import type { Analise, ConfigApp, CurriculoUpload, HistoricoItem, Melhoria } from "../types/api";

const BASE = import.meta.env.VITE_API_URL ?? "";

export class ErroApi extends Error {
  constructor(
    message: string,
    public status: number,
    public codigo?: string,
  ) {
    super(message);
  }
}

/** Extrai uma mensagem legível dos formatos de erro do FastAPI. */
function mensagemDeErro(corpo: unknown, status: number): { mensagem: string; codigo?: string } {
  const detail = (corpo as { detail?: unknown })?.detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail) && "mensagem" in detail) {
    const d = detail as { mensagem: string; codigo?: string };
    return { mensagem: d.mensagem, codigo: d.codigo };
  }
  if (Array.isArray(detail) && detail.length) {
    const campo = (detail[0] as { loc?: string[] }).loc?.at(-1);
    if (campo === "descricao_vaga") return { mensagem: "A descrição da vaga precisa ter pelo menos 80 caracteres.", codigo: "validacao" };
    return { mensagem: "Alguns dados enviados são inválidos. Revise e tente novamente.", codigo: "validacao" };
  }
  if (typeof detail === "string") return { mensagem: detail };
  if (status === 413) return { mensagem: "O arquivo é grande demais." };
  if (status >= 500) return { mensagem: "O servidor encontrou um erro. Tente novamente em instantes." };
  return { mensagem: `Erro inesperado (${status}).` };
}

async function requisicao<T>(caminho: string, init?: RequestInit): Promise<T> {
  let resposta: Response;
  try {
    resposta = await fetch(`${BASE}${caminho}`, init);
  } catch {
    throw new ErroApi(
      "Não foi possível conectar ao servidor. Verifique se o backend está em execução (porta 8000).",
      0,
      "sem_conexao",
    );
  }
  if (resposta.status === 204) return undefined as T;
  const corpo = await resposta.json().catch(() => null);
  if (!resposta.ok) {
    const { mensagem, codigo } = mensagemDeErro(corpo, resposta.status);
    throw new ErroApi(mensagem, resposta.status, codigo);
  }
  return corpo as T;
}

const json = (dados: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(dados),
});

export const api = {
  config: () => requisicao<ConfigApp>("/api/config"),

  enviarCurriculo: (arquivo: File) => {
    const form = new FormData();
    form.append("arquivo", arquivo);
    return requisicao<CurriculoUpload>("/api/resumes/upload", { method: "POST", body: form });
  },

  analisar: (resumeId: string, descricaoVaga: string) =>
    requisicao<Analise>("/api/analysis", json({ resume_id: resumeId, descricao_vaga: descricaoVaga })),

  obterAnalise: (id: string) => requisicao<Analise>(`/api/analysis/${encodeURIComponent(id)}`),

  historico: () => requisicao<HistoricoItem[]>("/api/analysis/history"),

  excluirAnalise: (id: string) => requisicao<void>(`/api/analysis/${encodeURIComponent(id)}`, { method: "DELETE" }),

  excluirHistorico: () => requisicao<void>("/api/analysis/history", { method: "DELETE" }),

  melhorarSecao: (secao: string, texto: string, analysisId?: string) =>
    requisicao<Melhoria>("/api/resumes/improve", json({ secao, texto, analysis_id: analysisId ?? null })),
};
