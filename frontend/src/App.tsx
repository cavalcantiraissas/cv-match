import { lazy, Suspense } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { Carregando } from "./components/ui";
import { AnalyzePage } from "./pages/AnalyzePage";
import { HistoryPage } from "./pages/HistoryPage";
import { LandingPage } from "./pages/LandingPage";

// O dashboard (com Recharts) e o editor só são baixados quando abertos.
const DashboardPage = lazy(() => import("./pages/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const ImprovePage = lazy(() => import("./pages/ImprovePage").then((m) => ({ default: m.ImprovePage })));

function NaoEncontrada() {
  return (
    <div className="mx-auto max-w-md px-4 py-28 text-center">
      <p className="text-sm font-medium text-brand-600">404</p>
      <h1 className="mt-2 text-2xl font-semibold text-zinc-900">Página não encontrada</h1>
      <Link to="/" className="mt-6 inline-block text-sm font-medium text-brand-700 hover:underline">
        Voltar ao início
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<LandingPage />} />
        <Route path="analisar" element={<AnalyzePage />} />
        <Route path="analises/:id" element={<Suspense fallback={<Carregando />}><DashboardPage /></Suspense>} />
        <Route path="analises/:id/melhorar" element={<Suspense fallback={<Carregando />}><ImprovePage /></Suspense>} />
        <Route path="historico" element={<HistoryPage />} />
        <Route path="*" element={<NaoEncontrada />} />
      </Route>
    </Routes>
  );
}
