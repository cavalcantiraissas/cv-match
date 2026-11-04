import { useCallback, useEffect, useState } from "react";

import { ErroApi } from "../services/api";

interface Estado<T> {
  dados: T | null;
  carregando: boolean;
  erro: string | null;
  recarregar: () => void;
}

/** Executa uma chamada à API ao montar (e quando `deps` mudam), com estados de carregamento e erro. */
export function useApi<T>(chamada: () => Promise<T>, deps: unknown[]): Estado<T> {
  const [dados, setDados] = useState<T | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [versao, setVersao] = useState(0);

  const executar = useCallback(chamada, deps);

  useEffect(() => {
    let ativo = true;
    setCarregando(true);
    setErro(null);
    executar()
      .then((r) => ativo && setDados(r))
      .catch((e: unknown) => ativo && setErro(e instanceof ErroApi ? e.message : "Erro inesperado."))
      .finally(() => ativo && setCarregando(false));
    return () => {
      ativo = false;
    };
  }, [executar, versao]);

  return { dados, carregando, erro, recarregar: () => setVersao((v) => v + 1) };
}
