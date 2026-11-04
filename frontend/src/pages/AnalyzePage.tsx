import { CheckCircle2, ChevronDown, FileText, Loader2, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { FileDropzone } from "../components/FileDropzone";
import { Aviso, Botao, Card, CardHeader, MensagemErro, Selo, cx } from "../components/ui";
import { ErroApi, api } from "../services/api";
import type { ConfigApp, CurriculoUpload } from "../types/api";

const MIN_VAGA = 80;

const VAGA_EXEMPLO = `Vaga: Pessoa Desenvolvedora Back-end Python Pleno

Responsabilidades:
- Desenvolver e manter APIs REST de alta disponibilidade.
- Participar de decisões de arquitetura e revisão de código.

Requisitos:
- 3+ anos de experiência com desenvolvimento back-end.
- Experiência com Python e FastAPI ou Django.
- Conhecimento em PostgreSQL.
- Experiência com Docker.
- Boa comunicação e trabalho em equipe.
- Formação superior em Ciência da Computação ou áreas afins.
- Inglês intermediário.

Diferenciais:
- Experiência com AWS ou Kubernetes.`;

export function AnalyzePage() {
  const navegar = useNavigate();
  const [config, setConfig] = useState<ConfigApp | null>(null);
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [curriculo, setCurriculo] = useState<CurriculoUpload | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [vaga, setVaga] = useState("");
  const [analisando, setAnalisando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [verPrevia, setVerPrevia] = useState(false);

  useEffect(() => {
    api.config().then(setConfig).catch(() => setConfig(null));
  }, []);

  const maxMb = config?.max_pdf_mb ?? 5;
  const maxVaga = config?.max_vaga_caracteres ?? 20000;

  async function selecionar(f: File) {
    setErro(null);
    setArquivo(f);
    setCurriculo(null);
    setEnviando(true);
    try {
      setCurriculo(await api.enviarCurriculo(f));
    } catch (e) {
      setArquivo(null);
      setErro(e instanceof ErroApi ? e.message : "Não foi possível enviar o arquivo.");
    } finally {
      setEnviando(false);
    }
  }

  async function analisar() {
    if (!curriculo) return;
    setErro(null);
    setAnalisando(true);
    try {
      const analise = await api.analisar(curriculo.resume_id, vaga.trim());
      navegar(`/analises/${analise.id}`);
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : "Não foi possível concluir a análise.");
      if (e instanceof ErroApi && e.codigo === "curriculo_nao_encontrado") {
        setArquivo(null);
        setCurriculo(null);
      }
      setAnalisando(false);
    }
  }

  const tamanhoVaga = vaga.trim().length;
  const podeAnalisar = !!curriculo && tamanhoVaga >= MIN_VAGA && tamanhoVaga <= maxVaga && !analisando;
  const secoesReconhecidas = curriculo?.secoes.filter((s) => s.chave !== "informacoes" && s.chave !== "geral") ?? [];

  if (analisando) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-28 text-center" role="status" aria-live="polite">
        <div className="relative mb-6">
          <div className="absolute inset-0 animate-ping rounded-full bg-brand-200 opacity-40" />
          <div className="relative grid size-16 place-items-center rounded-full bg-brand-600 text-white">
            <Loader2 className="size-7 animate-spin" aria-hidden />
          </div>
        </div>
        <h1 className="text-lg font-semibold text-zinc-900">Analisando a compatibilidade</h1>
        <ul className="mt-4 space-y-1.5 text-left text-sm text-zinc-500">
          <li>· Lendo as seções do currículo e os requisitos da vaga</li>
          <li>· Comparando competências, experiência e formação</li>
          <li>· Calculando o score e preparando as sugestões</li>
        </ul>
        <p className="mt-6 text-xs text-zinc-400">Na primeira execução o modelo semântico pode levar alguns segundos para carregar.</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Nova análise</h1>
      <p className="mt-1 text-sm text-zinc-500">Envie seu currículo e cole a descrição completa da vaga.</p>

      {erro && (
        <div className="mt-6">
          <MensagemErro mensagem={erro} />
        </div>
      )}

      <Card className="mt-6">
        <CardHeader
          titulo="1. Currículo"
          descricao="O arquivo é lido em memória e não é armazenado; guardamos só o texto, sem dados de contato."
          icone={<FileText className="size-4" />}
        />
        <div className="space-y-4 p-5">
          <FileDropzone
            arquivo={arquivo}
            maxMb={maxMb}
            desabilitado={enviando}
            onSelecionar={selecionar}
            onRemover={() => {
              setArquivo(null);
              setCurriculo(null);
            }}
            onErro={setErro}
          />
          {enviando && (
            <p className="flex items-center gap-2 text-sm text-zinc-500" role="status">
              <Loader2 className="size-4 animate-spin text-brand-600" aria-hidden /> Extraindo o texto do PDF…
            </p>
          )}
          {curriculo && (
            <div className="animate-fade-in space-y-3">
              <p className="flex items-center gap-2 text-sm text-zinc-700">
                <CheckCircle2 className="size-4 text-good" aria-hidden />
                Texto extraído: {curriculo.paginas} página(s), {curriculo.caracteres.toLocaleString("pt-BR")} caracteres.
              </p>
              <div className="flex flex-wrap gap-1.5">
                {secoesReconhecidas.map((s) => (
                  <Selo key={s.chave} tom="marca">{s.rotulo}</Selo>
                ))}
              </div>
              {curriculo.avisos.map((a) => (
                <Aviso key={a}>{a}</Aviso>
              ))}
              <button
                onClick={() => setVerPrevia((v) => !v)}
                className="inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:underline"
                aria-expanded={verPrevia}
              >
                {verPrevia ? "Ocultar" : "Ver"} prévia do texto extraído
                <ChevronDown className={cx("size-4 transition-transform", verPrevia && "rotate-180")} aria-hidden />
              </button>
              {verPrevia && (
                <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-100 bg-zinc-50 p-4 font-sans text-xs leading-relaxed text-zinc-700">
                  {curriculo.previa}
                  {curriculo.caracteres > curriculo.previa.length && "\n…"}
                </pre>
              )}
            </div>
          )}
        </div>
      </Card>

      <Card className="mt-6">
        <CardHeader
          titulo="2. Descrição da vaga"
          descricao="Inclua requisitos, diferenciais e atividades. Seções como “Requisitos” e “Diferenciais” melhoram a precisão."
          icone={<Sparkles className="size-4" />}
          acao={
            !vaga && (
              <button onClick={() => setVaga(VAGA_EXEMPLO)} className="shrink-0 text-xs font-medium text-brand-700 hover:underline">
                Usar vaga de exemplo
              </button>
            )
          }
        />
        <div className="p-5">
          <label htmlFor="vaga" className="sr-only">Descrição da vaga</label>
          <textarea
            id="vaga"
            value={vaga}
            onChange={(e) => setVaga(e.target.value)}
            rows={14}
            placeholder={"Cole aqui a descrição completa da vaga…\n\nRequisitos:\n- …\n\nDiferenciais:\n- …"}
            className="w-full resize-y rounded-lg border border-zinc-200 bg-white p-3 text-sm leading-relaxed text-zinc-800 outline-none transition-shadow placeholder:text-zinc-400 focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
          />
          <div className="mt-1.5 flex justify-between text-xs text-zinc-400">
            <span>{tamanhoVaga < MIN_VAGA ? `Mínimo de ${MIN_VAGA} caracteres` : "Pronto para analisar"}</span>
            <span className={cx("tabular-nums", tamanhoVaga > maxVaga && "text-red-600")}>
              {tamanhoVaga.toLocaleString("pt-BR")} / {maxVaga.toLocaleString("pt-BR")}
            </span>
          </div>
        </div>
      </Card>

      <div className="mt-6 flex flex-col-reverse items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-zinc-500">
          {!curriculo ? "Envie o currículo para continuar." : tamanhoVaga < MIN_VAGA ? "Cole a descrição da vaga para continuar." : " "}
        </p>
        <Botao onClick={analisar} disabled={!podeAnalisar} className="px-6 py-2.5">
          Analisar compatibilidade
        </Botao>
      </div>
    </div>
  );
}
