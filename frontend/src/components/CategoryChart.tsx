import { BarChart3, Table2 } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { CategoriaScore } from "../types/api";
import { formatarPercentual } from "../utils/format";
import { cx } from "./ui";

const COR_BARRA = "#5b4bd5";
const COR_BARRA_ATIVA = "#4a3cb0";

interface Linha {
  rotulo: string;
  score: number;
  peso: number;
  contribuicao: number;
  detalhe: string;
}

function Dica({ active, payload }: { active?: boolean; payload?: { payload: Linha }[] }) {
  if (!active || !payload?.length) return null;
  const l = payload[0].payload;
  return (
    <div className="max-w-xs rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs shadow-lg">
      <p className="font-semibold text-zinc-900">{l.rotulo}</p>
      <p className="mt-1 text-zinc-700">
        Score <span className="font-semibold tabular-nums">{formatarPercentual(l.score)}</span> · peso{" "}
        <span className="tabular-nums">{formatarPercentual(l.peso * 100)}</span> · soma{" "}
        <span className="tabular-nums">{l.contribuicao.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}</span> pts
      </p>
      <p className="mt-1 text-zinc-500">{l.detalhe}</p>
    </div>
  );
}

/** Desempenho por critério: barras horizontais de uma só cor, com alternativa em tabela. */
export function CategoryChart({ categorias }: { categorias: CategoriaScore[] }) {
  const [modo, setModo] = useState<"grafico" | "tabela">("grafico");
  const [ativa, setAtiva] = useState<number | null>(null);
  const aplicaveis: Linha[] = categorias
    .filter((c) => c.aplicavel && c.score !== null)
    .map((c) => ({ rotulo: c.rotulo, score: c.score as number, peso: c.peso_efetivo, contribuicao: c.contribuicao, detalhe: c.detalhe }));
  const naoAplicaveis = categorias.filter((c) => !c.aplicavel);

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <div className="inline-flex rounded-lg border border-zinc-200 p-0.5 text-xs" role="tablist" aria-label="Formato">
          {(["grafico", "tabela"] as const).map((m) => (
            <button
              key={m}
              role="tab"
              aria-selected={modo === m}
              onClick={() => setModo(m)}
              className={cx(
                "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium",
                modo === m ? "bg-zinc-900 text-white" : "text-zinc-600 hover:text-zinc-900",
              )}
            >
              {m === "grafico" ? <BarChart3 className="size-3.5" /> : <Table2 className="size-3.5" />}
              {m === "grafico" ? "Gráfico" : "Tabela"}
            </button>
          ))}
        </div>
      </div>

      {modo === "grafico" ? (
        <div style={{ height: Math.max(160, aplicaveis.length * 44 + 30) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={aplicaveis}
              layout="vertical"
              margin={{ top: 0, right: 12, bottom: 0, left: 0 }}
              barSize={14}
              onMouseLeave={() => setAtiva(null)}
            >
              <CartesianGrid horizontal={false} stroke="#ececec" />
              <XAxis
                type="number"
                domain={[0, 100]}
                ticks={[0, 25, 50, 75, 100]}
                tick={{ fontSize: 11, fill: "#71717a" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v: number) => `${v}%`}
              />
              <YAxis
                type="category"
                dataKey="rotulo"
                width={150}
                tick={{ fontSize: 12, fill: "#3f3f46" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<Dica />} cursor={{ fill: "#f4f4f5" }} />
              <Bar
                dataKey="score"
                radius={[0, 4, 4, 0]}
                background={{ fill: "#f4f3ff", radius: 4 }}
                onMouseEnter={(_, i) => setAtiva(i)}
                isAnimationActive
              >
                {aplicaveis.map((_, i) => (
                  <Cell key={i} fill={ativa === i ? COR_BARRA_ATIVA : COR_BARRA} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-zinc-500">
              <tr className="border-b border-zinc-100">
                <th className="py-2 pr-3 font-medium">Critério</th>
                <th className="py-2 pr-3 text-right font-medium">Score</th>
                <th className="py-2 pr-3 text-right font-medium">Peso</th>
                <th className="py-2 text-right font-medium">Pontos</th>
              </tr>
            </thead>
            <tbody>
              {categorias.map((c) => (
                <tr key={c.chave} className="border-b border-zinc-50 align-top">
                  <td className="py-2 pr-3">
                    <p className="font-medium text-zinc-800">{c.rotulo}</p>
                    <p className="text-xs text-zinc-500">{c.detalhe}</p>
                  </td>
                  <td className="py-2 pr-3 text-right tabular-nums">{c.score === null ? "—" : formatarPercentual(c.score)}</td>
                  <td className="py-2 pr-3 text-right tabular-nums text-zinc-600">
                    {formatarPercentual(c.peso_efetivo * 100, 1)}
                  </td>
                  <td className="py-2 text-right font-medium tabular-nums">
                    {c.contribuicao.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {naoAplicaveis.length > 0 && (
        <p className="mt-3 text-xs text-zinc-500">
          Fora do cálculo (a vaga não tem requisitos obrigatórios destes critérios; o peso foi redistribuído):{" "}
          {naoAplicaveis.map((c) => c.rotulo).join(", ")}.
        </p>
      )}
    </div>
  );
}
