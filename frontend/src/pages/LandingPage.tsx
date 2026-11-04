import { ArrowRight, BarChart3, FileSearch, KeyRound, ListChecks, PenLine, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

const FUNCIONALIDADES = [
  {
    icone: BarChart3,
    titulo: "Score explicável",
    texto: "Uma nota de 0 a 100 calculada por regras e similaridade semântica. Cada ponto aponta para um requisito e um trecho do seu currículo.",
  },
  {
    icone: ListChecks,
    titulo: "Requisito por requisito",
    texto: "Veja o que você já atende, o que está só parcialmente evidenciado e o que não aparece, com a justificativa de cada status.",
  },
  {
    icone: KeyRound,
    titulo: "Palavras-chave para ATS",
    texto: "Descubra quais termos da vaga faltam no currículo ou estão escritos de outra forma, para passar pelos filtros automáticos.",
  },
  {
    icone: PenLine,
    titulo: "Editor de currículo",
    texto: "Reescreva resumo, experiências e projetos com sugestões lado a lado. Nada é inventado: o texto parte do que você já escreveu.",
  },
  {
    icone: FileSearch,
    titulo: "Leitura do PDF",
    texto: "Extração do texto, identificação das seções e aviso quando o PDF é uma imagem digitalizada que precisa de OCR.",
  },
  {
    icone: ShieldCheck,
    titulo: "Privacidade",
    texto: "Contatos, idade, gênero e endereço são removidos antes da análise. O PDF não é guardado e você pode apagar tudo a qualquer momento.",
  },
];

const PASSOS = [
  ["Envie o currículo", "PDF com texto selecionável, até 5 MB."],
  ["Cole a descrição da vaga", "Quanto mais completa, mais precisa a análise."],
  ["Receba o diagnóstico", "Score, lacunas, palavras-chave e sugestões práticas."],
];

export function LandingPage() {
  return (
    <div className="animate-fade-in">
      <section className="relative overflow-hidden border-b border-zinc-200 bg-white">
        <div
          className="pointer-events-none absolute inset-0 opacity-60"
          style={{ backgroundImage: "radial-gradient(circle at 50% -20%, #e8e5ff 0, transparent 55%)" }}
          aria-hidden
        />
        <div className="relative mx-auto max-w-4xl px-4 py-20 text-center sm:px-6 sm:py-28">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
            Análise local, reproduzível e explicável
          </span>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-zinc-900 sm:text-6xl">
            Saiba o quanto seu currículo
            <span className="block text-brand-600">combina com a vaga.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-zinc-600">
            O CV Match compara seu currículo com a descrição de uma oportunidade, mostra quais requisitos você já evidencia,
            o que está faltando e como melhorar suas chances, sem inventar nada sobre você.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to="/analisar"
              className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700"
            >
              Analisar meu currículo <ArrowRight className="size-4" aria-hidden />
            </Link>
            <Link to="/historico" className="rounded-lg px-5 py-3 text-sm font-medium text-zinc-700 hover:bg-zinc-100">
              Ver análises anteriores
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="grid gap-4 sm:grid-cols-3">
          {PASSOS.map(([titulo, texto], i) => (
            <div key={titulo} className="flex gap-4 rounded-xl border border-zinc-200 bg-white p-5">
              <span className="grid size-8 shrink-0 place-items-center rounded-full bg-zinc-900 text-sm font-semibold text-white">{i + 1}</span>
              <div>
                <p className="font-medium text-zinc-900">{titulo}</p>
                <p className="mt-1 text-sm text-zinc-500">{texto}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <div className="mb-10 max-w-2xl">
          <h2 className="text-2xl font-semibold tracking-tight text-zinc-900">O que você recebe</h2>
          <p className="mt-2 text-zinc-600">
            A compatibilidade é calculada com regras determinísticas e análise semântica. A IA generativa é opcional e só
            ajuda a interpretar o resultado e reescrever textos.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FUNCIONALIDADES.map(({ icone: Icone, titulo, texto }) => (
            <div key={titulo} className="rounded-xl border border-zinc-200 bg-white p-6 transition-shadow hover:shadow-md">
              <div className="mb-4 inline-flex rounded-lg bg-brand-50 p-2 text-brand-600">
                <Icone className="size-5" aria-hidden />
              </div>
              <h3 className="font-semibold text-zinc-900">{titulo}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600">{texto}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
