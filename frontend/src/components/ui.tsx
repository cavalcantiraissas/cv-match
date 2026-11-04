import { AlertTriangle, CheckCircle2, CircleDashed, Loader2, RotateCw, XCircle } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function cx(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cx("rounded-xl border border-zinc-200 bg-white shadow-xs", className)}>{children}</section>;
}

export function CardHeader({ titulo, descricao, icone, acao }: { titulo: string; descricao?: string; icone?: ReactNode; acao?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-zinc-100 px-5 py-4">
      <div className="flex items-start gap-3">
        {icone && <div className="mt-0.5 text-brand-600">{icone}</div>}
        <div>
          <h2 className="text-[15px] font-semibold text-zinc-900">{titulo}</h2>
          {descricao && <p className="mt-0.5 text-sm text-zinc-500">{descricao}</p>}
        </div>
      </div>
      {acao}
    </div>
  );
}

type Variante = "primario" | "secundario" | "fantasma" | "perigo";

const VARIANTES: Record<Variante, string> = {
  primario: "bg-brand-600 text-white hover:bg-brand-700 shadow-sm disabled:bg-brand-300",
  secundario: "border border-zinc-200 bg-white text-zinc-800 hover:bg-zinc-50 disabled:text-zinc-400",
  fantasma: "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 disabled:text-zinc-300",
  perigo: "border border-red-200 bg-white text-red-700 hover:bg-red-50 disabled:text-red-300",
};

export function Botao({
  variante = "primario",
  carregando,
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variante?: Variante; carregando?: boolean }) {
  return (
    <button
      {...props}
      disabled={props.disabled || carregando}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:cursor-not-allowed",
        VARIANTES[variante],
        className,
      )}
    >
      {carregando && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Selo({ children, tom = "neutro", className }: { children: ReactNode; tom?: "neutro" | "marca" | "bom" | "alerta" | "ruim"; className?: string }) {
  const tons = {
    neutro: "bg-zinc-100 text-zinc-700 ring-zinc-200",
    marca: "bg-brand-50 text-brand-700 ring-brand-200",
    bom: "bg-green-50 text-green-800 ring-green-200",
    alerta: "bg-amber-50 text-amber-800 ring-amber-200",
    ruim: "bg-red-50 text-red-800 ring-red-200",
  };
  return (
    <span className={cx("inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset", tons[tom], className)}>
      {children}
    </span>
  );
}

/** Ícone + texto de status: a cor nunca aparece sozinha. */
export function IconeStatus({ status, className }: { status: "bom" | "parcial" | "ausente"; className?: string }) {
  if (status === "bom") return <CheckCircle2 className={cx("size-4 shrink-0 text-good", className)} aria-hidden />;
  if (status === "parcial") return <CircleDashed className={cx("size-4 shrink-0 text-amber-500", className)} aria-hidden />;
  return <XCircle className={cx("size-4 shrink-0 text-critical", className)} aria-hidden />;
}

export function Carregando({ texto = "Carregando…" }: { texto?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24 text-zinc-500" role="status">
      <Loader2 className="size-6 animate-spin text-brand-600" aria-hidden />
      <p className="text-sm">{texto}</p>
    </div>
  );
}

export function MensagemErro({ mensagem, tentarNovamente }: { mensagem: string; tentarNovamente?: () => void }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="flex-1">{mensagem}</div>
      {tentarNovamente && (
        <button onClick={tentarNovamente} className="inline-flex items-center gap-1 font-medium underline-offset-2 hover:underline">
          <RotateCw className="size-3.5" aria-hidden /> Tentar novamente
        </button>
      )}
    </div>
  );
}

export function Aviso({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" aria-hidden />
      <div>{children}</div>
    </div>
  );
}

export function Vazio({ icone, titulo, descricao, acao }: { icone: ReactNode; titulo: string; descricao: string; acao?: ReactNode }) {
  return (
    <div className="flex flex-col items-center px-6 py-16 text-center">
      <div className="mb-4 rounded-full bg-brand-50 p-3 text-brand-600">{icone}</div>
      <h3 className="font-semibold text-zinc-900">{titulo}</h3>
      <p className="mt-1 max-w-sm text-sm text-zinc-500">{descricao}</p>
      {acao && <div className="mt-5">{acao}</div>}
    </div>
  );
}
