import { ArrowLeft, Check, Copy, Info, PenLine, RotateCcw, Wand2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { Botao, Card, Carregando, MensagemErro, Selo, cx } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { ErroApi, api } from "../services/api";
import type { Melhoria } from "../types/api";
import { ROTULO_FONTE } from "../utils/format";

// Seções que podem ser reescritas, na ordem em que aparecem no seletor.
const EDITAVEIS: Record<string, string> = {
  resumo: "Resumo profissional",
  experiencia: "Experiência profissional",
  projetos: "Projetos",
  competencias: "Competências técnicas",
  certificacoes: "Certificações e cursos",
  formacao: "Formação acadêmica",
  geral: "Conteúdo do currículo",
};

export function ImprovePage() {
  const { id = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const { dados: analise, carregando, erro, recarregar } = useApi(() => api.obterAnalise(id), [id]);

  const secoes = useMemo(
    () => (analise?.curriculo.secoes ?? []).filter((s) => s.chave in EDITAVEIS).sort(
      (a, b) => Object.keys(EDITAVEIS).indexOf(a.chave) - Object.keys(EDITAVEIS).indexOf(b.chave),
    ),
    [analise],
  );
  const secaoAtual = secoes.find((s) => s.chave === params.get("secao")) ?? secoes[0];

  const [original, setOriginal] = useState("");
  const [resultado, setResultado] = useState<Melhoria | null>(null);
  const [sugerido, setSugerido] = useState("");
  const [gerando, setGerando] = useState(false);
  const [erroGerar, setErroGerar] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    setOriginal(secaoAtual?.texto ?? "");
    setResultado(null);
    setSugerido("");
    setErroGerar(null);
  }, [secaoAtual?.chave, secaoAtual?.texto]);

  async function gerar() {
    if (!secaoAtual) return;
    setGerando(true);
    setErroGerar(null);
    try {
      const r = await api.melhorarSecao(secaoAtual.chave, original, id);
      setResultado(r);
      setSugerido(r.sugerido);
    } catch (e) {
      setErroGerar(e instanceof ErroApi ? e.message : "Não foi possível gerar a sugestão.");
    } finally {
      setGerando(false);
    }
  }

  async function copiar() {
    try {
      await navigator.clipboard.writeText(sugerido);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1800);
    } catch {
      setErroGerar("Não foi possível copiar automaticamente. Selecione o texto e copie manualmente.");
    }
  }

  if (carregando) return <Carregando texto="Carregando currículo…" />;
  if (erro || !analise)
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <MensagemErro mensagem={erro ?? "Análise não encontrada."} tentarNovamente={recarregar} />
      </div>
    );

  const tamanhoOk = original.trim().length >= 10 && original.length <= 8000;

  return (
    <div className="animate-fade-in mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <Link to={`/analises/${id}`} className="inline-flex items-center gap-1 text-xs font-medium text-zinc-500 hover:text-zinc-800">
        <ArrowLeft className="size-3.5" /> Voltar ao resultado
      </Link>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">Melhorar meu currículo</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Escolha uma seção, ajuste o texto se quiser e gere uma versão mais clara e profissional para a vaga “{analise.vaga.cargo}”.
      </p>

      {secoes.length === 0 ? (
        <Card className="mt-6 p-6 text-sm text-zinc-600">Não identificamos seções editáveis neste currículo.</Card>
      ) : (
        <>
          <div className="mt-6 flex flex-wrap gap-1.5" role="tablist" aria-label="Seção do currículo">
            {secoes.map((s) => (
              <button
                key={s.chave}
                role="tab"
                aria-selected={s.chave === secaoAtual?.chave}
                onClick={() => setParams({ secao: s.chave })}
                className={cx(
                  "rounded-full px-3.5 py-1.5 text-sm font-medium ring-1 ring-inset transition-colors",
                  s.chave === secaoAtual?.chave ? "bg-brand-600 text-white ring-brand-600" : "bg-white text-zinc-700 ring-zinc-200 hover:bg-zinc-50",
                )}
              >
                {EDITAVEIS[s.chave]}
              </button>
            ))}
          </div>

          {erroGerar && <div className="mt-4"><MensagemErro mensagem={erroGerar} /></div>}

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card className="flex flex-col">
              <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-3">
                <h2 className="text-sm font-semibold text-zinc-900">Versão original</h2>
                {secaoAtual && original !== secaoAtual.texto && (
                  <button onClick={() => setOriginal(secaoAtual.texto)} className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-800">
                    <RotateCcw className="size-3" /> Restaurar
                  </button>
                )}
              </div>
              <label htmlFor="original" className="sr-only">Texto original</label>
              <textarea
                id="original"
                value={original}
                onChange={(e) => setOriginal(e.target.value)}
                className="min-h-80 flex-1 resize-y p-4 text-sm leading-relaxed text-zinc-700 outline-none"
              />
              <div className="flex items-center justify-between gap-3 border-t border-zinc-100 px-4 py-3">
                <span className="text-xs text-zinc-400">Você pode editar antes de gerar.</span>
                <Botao onClick={gerar} carregando={gerando} disabled={!tamanhoOk}>
                  {!gerando && <Wand2 className="size-4" aria-hidden />} Gerar sugestão
                </Botao>
              </div>
            </Card>

            <Card className="flex flex-col">
              <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-3">
                <h2 className="flex items-center gap-2 text-sm font-semibold text-zinc-900">
                  Versão sugerida {resultado && <Selo tom="marca">{ROTULO_FONTE[resultado.fonte] ?? resultado.fonte}</Selo>}
                </h2>
                {resultado && (
                  <button onClick={copiar} className="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline">
                    {copiado ? <Check className="size-3.5" /> : <Copy className="size-3.5" />} {copiado ? "Copiado" : "Copiar"}
                  </button>
                )}
              </div>
              {resultado ? (
                <>
                  <label htmlFor="sugerido" className="sr-only">Texto sugerido</label>
                  <textarea
                    id="sugerido"
                    value={sugerido}
                    onChange={(e) => setSugerido(e.target.value)}
                    className="min-h-80 flex-1 resize-y bg-brand-50/30 p-4 text-sm leading-relaxed text-zinc-800 outline-none"
                  />
                  <div className="border-t border-zinc-100 px-4 py-3 text-xs text-zinc-400">Edite livremente antes de copiar para o seu currículo.</div>
                </>
              ) : (
                <div className="flex flex-1 flex-col items-center justify-center p-10 text-center text-sm text-zinc-500">
                  <PenLine className="mb-3 size-6 text-zinc-300" aria-hidden />
                  {gerando ? "Gerando sugestão…" : "Clique em “Gerar sugestão” para ver a versão reescrita aqui."}
                </div>
              )}
            </Card>
          </div>

          {resultado && resultado.observacoes.length > 0 && (
            <Card className="animate-fade-in mt-4 p-4">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-zinc-900">
                <Info className="size-4 text-brand-600" aria-hidden /> Observações
              </h3>
              <ul className="space-y-1.5 text-sm text-zinc-600">
                {resultado.observacoes.map((o) => (
                  <li key={o} className={cx(o.startsWith("Atenção") && "font-medium text-amber-800")}>· {o}</li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
