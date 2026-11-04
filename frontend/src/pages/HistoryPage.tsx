import { ChevronRight, History, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Botao, Card, Carregando, MensagemErro, Vazio } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { ErroApi, api } from "../services/api";
import { COR_FAIXA, faixaDoScore, formatarData } from "../utils/format";

export function HistoryPage() {
  const { dados, carregando, erro, recarregar } = useApi(() => api.historico(), []);
  const [excluindo, setExcluindo] = useState<string | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);

  async function executar(chave: string, acao: () => Promise<void>, confirmacao: string) {
    if (!confirm(confirmacao)) return;
    setExcluindo(chave);
    setErroAcao(null);
    try {
      await acao();
      recarregar();
    } catch (e) {
      setErroAcao(e instanceof ErroApi ? e.message : "Não foi possível excluir.");
    } finally {
      setExcluindo(null);
    }
  }

  return (
    <div className="animate-fade-in mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Histórico</h1>
          <p className="mt-1 text-sm text-zinc-500">Análises anteriores. Excluir uma análise apaga também o texto do currículo associado.</p>
        </div>
        {!!dados?.length && (
          <Botao
            variante="perigo"
            carregando={excluindo === "todos"}
            onClick={() => executar("todos", api.excluirHistorico, "Excluir todo o histórico e os currículos armazenados? Essa ação não pode ser desfeita.")}
          >
            {excluindo !== "todos" && <Trash2 className="size-4" aria-hidden />} Excluir tudo
          </Botao>
        )}
      </div>

      {erroAcao && <div className="mt-4"><MensagemErro mensagem={erroAcao} /></div>}

      <Card className="mt-6">
        {carregando ? (
          <Carregando texto="Carregando histórico…" />
        ) : erro ? (
          <div className="p-5"><MensagemErro mensagem={erro} tentarNovamente={recarregar} /></div>
        ) : !dados?.length ? (
          <Vazio
            icone={<History className="size-6" />}
            titulo="Nenhuma análise ainda"
            descricao="Quando você analisar um currículo, o resultado aparece aqui para consultar depois."
            acao={
              <Link to="/analisar" className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
                <Plus className="size-4" /> Nova análise
              </Link>
            }
          />
        ) : (
          <ul className="divide-y divide-zinc-100">
            {dados.map((item) => {
              const cor = COR_FAIXA[faixaDoScore(item.score)];
              return (
                <li key={item.id} className="group flex items-center gap-2 pr-3">
                  <Link to={`/analises/${item.id}`} className="flex min-w-0 flex-1 items-center gap-4 px-5 py-4 hover:bg-zinc-50">
                    <div
                      className="grid size-12 shrink-0 place-items-center rounded-full text-sm font-semibold tabular-nums text-zinc-900"
                      style={{ background: `conic-gradient(${cor.traco} ${item.score * 3.6}deg, ${cor.trilha} 0)` }}
                      aria-hidden
                    >
                      <span className="grid size-9 place-items-center rounded-full bg-white">{item.score}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-zinc-900">{item.cargo}</p>
                      <p className="text-xs text-zinc-500">
                        <span className="sr-only">Score {item.score}. </span>
                        {item.classificacao} · {formatarData(item.criado_em)}
                      </p>
                    </div>
                    <ChevronRight className="size-4 text-zinc-300 group-hover:text-zinc-500" aria-hidden />
                  </Link>
                  <Botao
                    variante="fantasma"
                    className="px-2"
                    carregando={excluindo === item.id}
                    aria-label={`Excluir análise ${item.cargo}`}
                    onClick={() => executar(item.id, () => api.excluirAnalise(item.id), `Excluir a análise “${item.cargo}”?`)}
                  >
                    {excluindo !== item.id && <Trash2 className="size-4" aria-hidden />}
                  </Botao>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
