import { useEffect, useState } from "react";

import { COR_FAIXA, faixaDoScore } from "../utils/format";

/** Medidor circular: o preenchimento carrega a faixa; a trilha é um tom claro da mesma cor. */
export function ScoreRing({ score, classificacao, tamanho = 184 }: { score: number; classificacao: string; tamanho?: number }) {
  const [animado, setAnimado] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setAnimado(score));
    return () => cancelAnimationFrame(id);
  }, [score]);

  const espessura = 12;
  const raio = (tamanho - espessura) / 2;
  const circ = 2 * Math.PI * raio;
  const cores = COR_FAIXA[faixaDoScore(score)];

  return (
    <div className="relative" style={{ width: tamanho, height: tamanho }} role="img" aria-label={`Score ${score} de 100: ${classificacao}`}>
      <svg width={tamanho} height={tamanho} className="-rotate-90">
        <circle cx={tamanho / 2} cy={tamanho / 2} r={raio} fill="none" stroke={cores.trilha} strokeWidth={espessura} />
        <circle
          cx={tamanho / 2}
          cy={tamanho / 2}
          r={raio}
          fill="none"
          stroke={cores.traco}
          strokeWidth={espessura}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - animado / 100)}
          style={{ transition: "stroke-dashoffset 900ms cubic-bezier(.2,.8,.2,1)" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-5xl font-semibold tracking-tight text-zinc-900 tabular-nums">{score}</span>
        <span className="text-xs font-medium text-zinc-500">de 100</span>
      </div>
    </div>
  );
}
