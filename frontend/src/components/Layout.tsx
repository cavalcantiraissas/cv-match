import { FileSearch, History, Menu, ScanSearch, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { cx } from "./ui";

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight text-zinc-900">
      <span className="grid size-7 place-items-center rounded-lg bg-brand-600 text-white shadow-sm">
        <ScanSearch className="size-4" aria-hidden />
      </span>
      CV Match
    </Link>
  );
}

const LINKS = [
  { para: "/analisar", rotulo: "Nova análise", icone: FileSearch },
  { para: "/historico", rotulo: "Histórico", icone: History },
];

export function Layout() {
  const [aberto, setAberto] = useState(false);

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-30 border-b border-zinc-200/80 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Logo />
          <nav className="hidden items-center gap-1 sm:flex" aria-label="Principal">
            {LINKS.map(({ para, rotulo, icone: Icone }) => (
              <NavLink
                key={para}
                to={para}
                className={({ isActive }) =>
                  cx(
                    "inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                    isActive ? "bg-brand-50 text-brand-700" : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900",
                  )
                }
              >
                <Icone className="size-4" aria-hidden />
                {rotulo}
              </NavLink>
            ))}
          </nav>
          <button
            className="rounded-lg p-2 text-zinc-600 hover:bg-zinc-100 sm:hidden"
            onClick={() => setAberto((a) => !a)}
            aria-label={aberto ? "Fechar menu" : "Abrir menu"}
            aria-expanded={aberto}
          >
            {aberto ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
        {aberto && (
          <nav className="border-t border-zinc-100 px-4 py-2 sm:hidden" aria-label="Principal (celular)">
            {LINKS.map(({ para, rotulo, icone: Icone }) => (
              <NavLink
                key={para}
                to={para}
                onClick={() => setAberto(false)}
                className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100"
              >
                <Icone className="size-4" aria-hidden />
                {rotulo}
              </NavLink>
            ))}
          </nav>
        )}
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <span>CV Match · análise explicável de compatibilidade entre currículo e vaga</span>
          <span>Dados de contato e características pessoais não são usados no cálculo.</span>
        </div>
      </footer>
    </div>
  );
}
