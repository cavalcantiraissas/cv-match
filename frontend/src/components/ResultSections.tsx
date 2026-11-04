import { ArrowUpRight, ChevronDown, Lightbulb, Quote } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import type { CompetenciaAvaliada, PalavraChave, RequisitoAvaliado, Sugestao } from "../types/api";
import { ROTULO_EVIDENCIA, ROTULO_PRIORIDADE } from "../utils/format";
import { IconeStatus, Selo, cx } from "./ui";

const ROTULO_STATUS_REQ = { atendido: "Atendido", parcial: "Parcialmente atendido", nao_identificado: "Não identificado" } as const;
const ICONE_STATUS_REQ = { atendido: "bom", parcial: "parcial", nao_identificado: "ausente" } as const;

function Trecho({ texto }: { texto: string }) {
  return (
    <p className="mt-2 flex gap-2 rounded-md bg-zinc-50 px-3 py-2 text-xs leading-relaxed text-zinc-600">
      <Quote className="mt-0.5 size-3 shrink-0 text-zinc-400" aria-hidden />
      <span>{texto}</span>
    </p>
  );
}

// --- D. Requisitos ----------------------------------------------------------------

type FiltroReq = "todos" | RequisitoAvaliado["status"];

export function RequirementList({ requisitos }: { requisitos: RequisitoAvaliado[] }) {
  const [filtro, setFiltro] = useState<FiltroReq>("todos");
  const [aberto, setAberto] = useState<number | null>(null);
  const contagem = useMemo(
    () => ({
      todos: requisitos.length,
      atendido: requisitos.filter((r) => r.status === "atendido").length,
      parcial: requisitos.filter((r) => r.status === "parcial").length,
      nao_identificado: requisitos.filter((r) => r.status === "nao_identificado").length,
    }),
    [requisitos],
  );
  const visiveis = requisitos.map((r, i) => ({ r, i })).filter(({ r }) => filtro === "todos" || r.status === filtro);

  if (!requisitos.length) return <p className="px-5 py-8 text-sm text-zinc-500">Nenhum requisito identificado na descrição da vaga.</p>;

  return (
    <div>
      <div className="flex flex-wrap gap-1.5 px-5 pt-4" role="tablist" aria-label="Filtrar requisitos">
        {(["todos", "atendido", "parcial", "nao_identificado"] as const).map((f) => (
          <button
            key={f}
            role="tab"
            aria-selected={filtro === f}
            onClick={() => setFiltro(f)}
            className={cx(
              "rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset transition-colors",
              filtro === f ? "bg-zinc-900 text-white ring-zinc-900" : "bg-white text-zinc-600 ring-zinc-200 hover:bg-zinc-50",
            )}
          >
            {f === "todos" ? "Todos" : ROTULO_STATUS_REQ[f]} <span className="tabular-nums opacity-70">{contagem[f]}</span>
          </button>
        ))}
      </div>
      <ul className="divide-y divide-zinc-100 px-2 py-2">
        {visiveis.map(({ r, i }) => (
          <li key={i}>
            <button
              className="flex w-full items-start gap-3 rounded-lg px-3 py-3 text-left hover:bg-zinc-50"
              onClick={() => setAberto(aberto === i ? null : i)}
              aria-expanded={aberto === i}
            >
              <IconeStatus status={ICONE_STATUS_REQ[r.status]} className="mt-0.5" />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-zinc-800">{r.texto}</p>
                <div className="mt-1 flex flex-wrap items-center gap-1.5">
                  <span className="text-xs font-medium text-zinc-600">{ROTULO_STATUS_REQ[r.status]}</span>
                  <span className="text-zinc-300">·</span>
                  <span className="text-xs text-zinc-500">{r.obrigatorio ? "Obrigatório" : "Desejável"}</span>
                </div>
              </div>
              <ChevronDown className={cx("mt-1 size-4 shrink-0 text-zinc-400 transition-transform", aberto === i && "rotate-180")} aria-hidden />
            </button>
            {aberto === i && (
              <div className="animate-fade-in px-10 pb-4 text-sm text-zinc-600">
                <p>{r.justificativa}</p>
                {r.trecho && <Trecho texto={r.trecho} />}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

// --- C. Competências ------------------------------------------------------------

const COLUNAS = [
  { status: "encontrada", titulo: "Encontradas", icone: "bom" },
  { status: "parcial", titulo: "Parcialmente evidenciadas", icone: "parcial" },
  { status: "nao_identificada", titulo: "Não identificadas", icone: "ausente" },
] as const;

export function SkillsBoard({ competencias }: { competencias: CompetenciaAvaliada[] }) {
  const [selecionada, setSelecionada] = useState<CompetenciaAvaliada | null>(null);
  if (!competencias.length) return <p className="px-5 py-8 text-sm text-zinc-500">A vaga não cita competências do nosso catálogo.</p>;

  return (
    <div className="p-5">
      <div className="grid gap-4 md:grid-cols-3">
        {COLUNAS.map((col) => {
          const itens = competencias.filter((c) => c.status === col.status);
          return (
            <div key={col.status} className="rounded-lg border border-zinc-100 bg-zinc-50/60 p-3">
              <h3 className="mb-2.5 flex items-center gap-2 text-xs font-semibold text-zinc-700">
                <IconeStatus status={col.icone} /> {col.titulo}
                <span className="ml-auto tabular-nums text-zinc-400">{itens.length}</span>
              </h3>
              {itens.length === 0 ? (
                <p className="text-xs text-zinc-400">Nenhuma</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {itens.map((c) => (
                    <button
                      key={c.nome}
                      onClick={() => setSelecionada(selecionada?.nome === c.nome ? null : c)}
                      className={cx(
                        "rounded-md border bg-white px-2 py-1 text-xs font-medium transition-colors",
                        selecionada?.nome === c.nome ? "border-brand-400 text-brand-700 ring-2 ring-brand-100" : "border-zinc-200 text-zinc-700 hover:border-zinc-300",
                      )}
                      title={c.justificativa}
                    >
                      {c.nome}
                      {!c.obrigatoria && <span className="ml-1 text-zinc-400">· desejável</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {selecionada ? (
        <div className="animate-fade-in mt-4 rounded-lg border border-zinc-200 p-4 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-zinc-900">{selecionada.nome}</span>
            <Selo tom="marca">{ROTULO_EVIDENCIA[selecionada.evidencia]}</Selo>
            <Selo>{selecionada.obrigatoria ? "Obrigatória" : "Desejável"}</Selo>
          </div>
          <p className="mt-2 text-zinc-600">{selecionada.justificativa}</p>
          {selecionada.trecho && <Trecho texto={selecionada.trecho} />}
        </div>
      ) : (
        <p className="mt-3 text-xs text-zinc-500">Clique em uma competência para ver a evidência encontrada no currículo.</p>
      )}
    </div>
  );
}

// --- F. Palavras-chave ATS ------------------------------------------------------------

export function KeywordPanel({ palavras }: { palavras: PalavraChave[] }) {
  if (!palavras.length) return <p className="px-5 py-8 text-sm text-zinc-500">Nenhuma palavra-chave técnica identificada na vaga.</p>;
  const presentes = palavras.filter((p) => p.status === "presente");
  const ajustes = palavras.filter((p) => p.status !== "presente");

  return (
    <div className="grid gap-6 p-5 lg:grid-cols-2">
      <div>
        <h3 className="mb-2 flex items-center gap-2 text-xs font-semibold text-zinc-700">
          <IconeStatus status="bom" /> Encontradas no currículo ({presentes.length})
        </h3>
        {presentes.length ? (
          <div className="flex flex-wrap gap-1.5">
            {presentes.map((p) => (
              <Selo key={p.termo} tom="bom">{p.termo_na_vaga}</Selo>
            ))}
          </div>
        ) : (
          <p className="text-xs text-zinc-400">Nenhuma palavra-chave da vaga aparece exatamente como escrita.</p>
        )}
      </div>
      <div>
        <h3 className="mb-2 flex items-center gap-2 text-xs font-semibold text-zinc-700">
          <IconeStatus status="ausente" /> Ausentes ou com outra grafia ({ajustes.length})
        </h3>
        <ul className="space-y-2">
          {ajustes.map((p) => (
            <li key={p.termo} className="rounded-lg border border-zinc-100 px-3 py-2">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-sm font-medium text-zinc-800">{p.termo_na_vaga}</span>
                <Selo tom={p.status === "variacao" ? "alerta" : "neutro"}>{p.status === "variacao" ? "Outra grafia" : "Ausente"}</Selo>
                {p.obrigatoria && <Selo tom="marca">Obrigatória</Selo>}
              </div>
              {p.sugestao && <p className="mt-1 text-xs text-zinc-500">{p.sugestao}</p>}
            </li>
          ))}
          {!ajustes.length && <p className="text-xs text-zinc-400">Todas as palavras-chave da vaga aparecem no currículo.</p>}
        </ul>
      </div>
    </div>
  );
}

// --- E. Sugestões ---------------------------------------------------------------------

const TOM_PRIORIDADE = { alta: "ruim", media: "alerta", baixa: "neutro" } as const;
const SECOES_EDITAVEIS = new Set(["resumo", "experiencia", "projetos", "competencias"]);

export function SuggestionList({ sugestoes, analiseId }: { sugestoes: Sugestao[]; analiseId: string }) {
  return (
    <ul className="divide-y divide-zinc-100">
      {sugestoes.map((s, i) => (
        <li key={i} className="flex gap-3 px-5 py-4">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-brand-500" aria-hidden />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-zinc-900">{s.titulo}</p>
              <Selo tom={TOM_PRIORIDADE[s.prioridade]}>Prioridade {ROTULO_PRIORIDADE[s.prioridade].toLowerCase()}</Selo>
            </div>
            <p className="mt-1 text-sm leading-relaxed text-zinc-600">{s.descricao}</p>
            {s.secao && SECOES_EDITAVEIS.has(s.secao) && (
              <Link
                to={`/analises/${analiseId}/melhorar?secao=${s.secao}`}
                className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline"
              >
                Reescrever esta seção <ArrowUpRight className="size-3" aria-hidden />
              </Link>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
