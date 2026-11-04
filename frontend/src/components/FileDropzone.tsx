import { FileText, UploadCloud, X } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import { formatarTamanho } from "../utils/format";
import { cx } from "./ui";

interface Props {
  arquivo: File | null;
  maxMb: number;
  desabilitado?: boolean;
  onSelecionar: (arquivo: File) => void;
  onRemover: () => void;
  onErro: (mensagem: string) => void;
}

export function FileDropzone({ arquivo, maxMb, desabilitado, onSelecionar, onRemover, onErro }: Props) {
  const entrada = useRef<HTMLInputElement>(null);
  const [arrastando, setArrastando] = useState(false);

  function validar(f: File | undefined) {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) return onErro("Envie o currículo em formato PDF.");
    if (f.size > maxMb * 1024 * 1024) return onErro(`O arquivo tem ${formatarTamanho(f.size)}. O limite é ${maxMb} MB.`);
    onSelecionar(f);
  }

  function soltar(e: DragEvent) {
    e.preventDefault();
    setArrastando(false);
    if (!desabilitado) validar(e.dataTransfer.files[0]);
  }

  if (arquivo) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-zinc-200 bg-white p-4">
        <div className="grid size-10 place-items-center rounded-lg bg-brand-50 text-brand-600">
          <FileText className="size-5" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-zinc-900">{arquivo.name}</p>
          <p className="text-xs text-zinc-500">{formatarTamanho(arquivo.size)}</p>
        </div>
        <button
          onClick={onRemover}
          disabled={desabilitado}
          className="rounded-lg p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 disabled:opacity-40"
          aria-label="Remover arquivo"
        >
          <X className="size-4" />
        </button>
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setArrastando(true);
      }}
      onDragLeave={() => setArrastando(false)}
      onDrop={soltar}
      className={cx(
        "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors",
        arrastando ? "border-brand-400 bg-brand-50" : "border-zinc-200 bg-white hover:border-zinc-300",
      )}
    >
      <UploadCloud className="mb-3 size-8 text-brand-500" aria-hidden />
      <p className="text-sm font-medium text-zinc-800">Arraste o PDF do seu currículo aqui</p>
      <p className="mt-1 text-xs text-zinc-500">ou</p>
      <button
        type="button"
        onClick={() => entrada.current?.click()}
        disabled={desabilitado}
        className="mt-2 rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
      >
        Escolher arquivo
      </button>
      <p className="mt-3 text-xs text-zinc-400">Somente PDF com texto selecionável · até {maxMb} MB</p>
      <input
        ref={entrada}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        onChange={(e) => {
          validar(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    </div>
  );
}
