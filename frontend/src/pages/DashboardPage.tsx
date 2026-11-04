import {
  ArrowLeft,
  BarChart3,
  Briefcase,
  ChevronDown,
  KeyRound,
  Lightbulb,
  ListChecks,
  PenLine,
  Sigma,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { CategoryChart } from "../components/CategoryChart";
import { KeywordPanel, RequirementList, SkillsBoard, SuggestionList } from "../components/ResultSections";
import { ScoreRing } from "../components/ScoreRing";
import { Aviso, Botao, Card, CardHeader, Carregando, MensagemErro, Selo, cx } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { ErroApi, api } from "../services/api";
import type { Analise } from "../types/api";
import { ROTULO_FONTE, ROTULO_MOTOR, formatarData, formatarPercentual } from "../utils/format";

function Indicador({ rotulo, valor, detalhe }: { rotulo: string; valor: string; detalhe?: string }) {
  return (
    <div className="rounded-lg bg-zinc-50 px-3 py-2.5">
      <p className="text-xs text-zinc-500">{rotulo}</p>
      <p className="mt-0.5 text-lg font-semibold tabular-nums text-zinc-900">{valor}</p>
      {detalhe && <p className="text-xs text-zinc-500">{detalhe}</p>}
    </div>
  );
}

function ResumoVaga({ analise }: { analise: Analise }) {
  const v = analise.vaga;
  const linhas: [string, string | null][] = [
    ["Cargo", v.cargo],
    ["Nível", v.nivel],
    ["Experiência pedida", v.anos_experiencia ? `${v.anos_experiencia}+ anos` : null],
    ["Formação", v.formacao],
    ["Idiomas", v.idiomas.join(", ") || null],
    ["Competências técnicas", v.competencias_tecnicas.join(", ") || null],
    ["Ferramentas e tecnologias", v.ferramentas.join(", ") || null],
    ["Competências comportamentais", v.competencias_comportamentais.join(", ") || null],
    ["Certificações", v.certificacoes.join(", ") || null],
  ];
  const c = analise.curriculo;
  return (
    <div className="grid gap-6 p-5 md:grid-cols-2">
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">Identificado na vaga</h3>
        <dl className="space-y-2 text-sm">
          {linhas.map(([rotulo, valor]) => (
            <div key={rotulo} className="grid grid-cols-[150px_1fr] gap-2">
              <dt className="text-zinc-500">{rotulo}</dt>
              <dd className="text-zinc-800">{valor ?? <span className="text-zinc-400">Não informado</span>}</dd>
            </div>
          ))}
        </dl>
        {v.diferenciais.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-medium text-zinc-500">Desejáveis / diferenciais</p>
            <ul className="mt-1 list-inside list-disc text-sm text-zinc-700">
              {v.diferenciais.map((d) => <li key={d}>{d}</li>)}
            </ul>
          </div>
        )}
      </div>
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">Identificado no currículo</h3>
        <dl className="space-y-2 text-sm">
          <div className="grid grid-cols-[150px_1fr] gap-2">
            <dt className="text-zinc-500">Experiência</dt>
            <dd className="text-zinc-800">
              {c.anos_experiencia !== null ? `${c.anos_experiencia.toLocaleString("pt-BR")} anos (${c.anos_origem})` : "Não identificada"}
            </dd>
          </div>
          <div className="grid grid-cols-[150px_1fr] gap-2">
            <dt className="text-zinc-500">Formação</dt>
            <dd className="text-zinc-800">{c.formacao}</dd>
          </div>
          <div className="grid grid-cols-[150px_1fr] gap-2">
            <dt className="text-zinc-500">Idiomas</dt>
            <dd className="text-zinc-800">{c.idiomas.join(", ") || "Não identificados"}</dd>
          </div>
          <div className="grid grid-cols-[150px_1fr] gap-2">
            <dt className="text-zinc-500">Certificações</dt>
            <dd className="text-zinc-800">{c.certificacoes.join(", ") || "Não identificadas"}</dd>
          </div>
          <div className="grid grid-cols-[150px_1fr] gap-2">
            <dt className="text-zinc-500">Seções</dt>
            <dd className="text-zinc-800">{c.secoes.filter((s) => s.chave !== "informacoes").map((s) => s.rotulo).join(", ")}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

function ComoCalculamos({ analise }: { analise: Analise }) {
  const [aberto, setAberto] = useState(false);
  return (
    <Card>
      <button className="flex w-full items-center justify-between px-5 py-4 text-left" onClick={() => setAberto((a) => !a)} aria-expanded={aberto}>
        <span className="flex items-center gap-3">
          <Sigma className="size-4 text-brand-600" aria-hidden />
          <span className="text-[15px] font-semibold text-zinc-900">Como este score foi calculado</span>
        </span>
        <ChevronDown className={cx("size-4 text-zinc-400 transition-transform", aberto && "rotate-180")} aria-hidden />
      </button>
      {aberto && (
        <div className="animate-fade-in space-y-3 border-t border-zinc-100 px-5 py-4 text-sm leading-relaxed text-zinc-600">
          <p>
            O score é a média ponderada dos critérios abaixo. Ele é calculado por regras determinísticas e similaridade
            semântica ({ROTULO_MOTOR[analise.motor_semantico] ?? analise.motor_semantico}): a mesma entrada sempre produz o
            mesmo resultado. A IA generativa não participa do cálculo.
          </p>
          <ul className="list-inside list-disc space-y-1">
            <li>Competências usadas em experiências ou projetos valem 100%; apenas listadas, 60%; tecnologia equivalente, 40%.</li>
            <li>Requisitos desejáveis só aumentam o score quando atendidos, nunca o reduzem.</li>
            <li>Critérios sem requisitos obrigatórios na vaga saem do cálculo e seu peso é redistribuído.</li>
            <li>Idade, gênero, foto, endereço e dados de contato são removidos e não influenciam a nota.</li>
          </ul>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {analise.categorias.map((c) => (
              <Selo key={c.chave}>
                {c.rotulo}: {formatarPercentual(c.peso * 100)}
              </Selo>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

export function DashboardPage() {
  const { id = "" } = useParams();
  const navegar = useNavigate();
  const { dados: analise, carregando, erro, recarregar } = useApi(() => api.obterAnalise(id), [id]);
  const [excluindo, setExcluindo] = useState(false);
  const [erroExcluir, setErroExcluir] = useState<string | null>(null);

  async function excluir() {
    if (!confirm("Excluir esta análise e o currículo associado? Essa ação não pode ser desfeita.")) return;
    setExcluindo(true);
    try {
      await api.excluirAnalise(id);
      navegar("/historico");
    } catch (e) {
      setErroExcluir(e instanceof ErroApi ? e.message : "Não foi possível excluir.");
      setExcluindo(false);
    }
  }

  if (carregando) return <Carregando texto="Carregando análise…" />;
  if (erro || !analise)
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <MensagemErro mensagem={erro ?? "Análise não encontrada."} tentarNovamente={recarregar} />
        <Link to="/historico" className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:underline">
          <ArrowLeft className="size-4" /> Voltar ao histórico
        </Link>
      </div>
    );

  const obrig = analise.requisitos.filter((r) => r.obrigatorio);
  const obrigAtendidos = obrig.filter((r) => r.status === "atendido").length;
  const encontradas = analise.competencias.filter((c) => c.status === "encontrada").length;
  const ats = analise.palavras_chave;
  const atsPresentes = ats.filter((p) => p.status === "presente").length;

  return (
    <div className="animate-fade-in mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <Link to="/historico" className="inline-flex items-center gap-1 text-xs font-medium text-zinc-500 hover:text-zinc-800">
            <ArrowLeft className="size-3.5" /> Histórico
          </Link>
          <h1 className="mt-1 truncate text-2xl font-semibold tracking-tight text-zinc-900">{analise.vaga.cargo}</h1>
          <p className="mt-1 text-sm text-zinc-500">Analisado em {formatarData(analise.criado_em)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/analises/${analise.id}/melhorar`}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
          >
            <PenLine className="size-4" aria-hidden /> Melhorar meu currículo
          </Link>
          <Botao variante="secundario" onClick={() => navegar("/analisar")}>Nova análise</Botao>
          <Botao variante="perigo" onClick={excluir} carregando={excluindo} aria-label="Excluir análise">
            {!excluindo && <Trash2 className="size-4" aria-hidden />}
          </Botao>
        </div>
      </div>

      {erroExcluir && <div className="mt-4"><MensagemErro mensagem={erroExcluir} /></div>}
      {analise.avisos.length > 0 && (
        <div className="mt-6 space-y-2">
          {analise.avisos.map((a) => <Aviso key={a}>{a}</Aviso>)}
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <Card>
          <CardHeader titulo="Score de compatibilidade" icone={<Sparkles className="size-4" />} />
          <div className="flex flex-col items-center p-6">
            <ScoreRing score={analise.score} classificacao={analise.classificacao} />
            <p className="mt-4 text-lg font-semibold text-zinc-900">{analise.classificacao}</p>
            <div className="mt-6 grid w-full grid-cols-2 gap-2">
              <Indicador rotulo="Obrigatórios atendidos" valor={`${obrigAtendidos}/${obrig.length}`} />
              <Indicador rotulo="Competências encontradas" valor={`${encontradas}/${analise.competencias.length}`} />
              <Indicador rotulo="Palavras-chave ATS" valor={`${atsPresentes}/${ats.length}`} />
              <Indicador
                rotulo="Experiência"
                valor={analise.curriculo.anos_experiencia !== null ? `${analise.curriculo.anos_experiencia.toLocaleString("pt-BR")} anos` : "—"}
                detalhe={analise.vaga.anos_experiencia ? `vaga pede ${analise.vaga.anos_experiencia}+` : undefined}
              />
            </div>
          </div>
        </Card>
        <Card>
          <CardHeader
            titulo="Compatibilidade por critério"
            descricao="Passe o mouse nas barras para ver o detalhe de cada critério."
            icone={<BarChart3 className="size-4" />}
          />
          <div className="p-5">
            <CategoryChart categorias={analise.categorias} />
          </div>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader
            titulo="Análise dos requisitos"
            descricao="Clique em um requisito para ver a justificativa e o trecho do currículo."
            icone={<ListChecks className="size-4" />}
          />
          <RequirementList requisitos={analise.requisitos} />
        </Card>
        <Card>
          <CardHeader
            titulo="Sugestões de melhoria"
            descricao={`Fonte: ${ROTULO_FONTE[analise.fonte_sugestoes] ?? analise.fonte_sugestoes}. Inclua apenas o que for verdadeiro.`}
            icone={<Lightbulb className="size-4" />}
          />
          <SuggestionList sugestoes={analise.sugestoes} analiseId={analise.id} />
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader titulo="Competências" descricao="Exigidas ou citadas na vaga, conforme a evidência no currículo." icone={<Sparkles className="size-4" />} />
        <SkillsBoard competencias={analise.competencias} />
      </Card>

      <Card className="mt-6">
        <CardHeader
          titulo="Palavras-chave para ATS"
          descricao="Sistemas de triagem costumam buscar os termos exatos da vaga."
          icone={<KeyRound className="size-4" />}
        />
        <KeywordPanel palavras={analise.palavras_chave} />
      </Card>

      <Card className="mt-6">
        <CardHeader titulo="O que foi identificado" icone={<Briefcase className="size-4" />} />
        <ResumoVaga analise={analise} />
      </Card>

      <div className="mt-6">
        <ComoCalculamos analise={analise} />
      </div>
    </div>
  );
}
