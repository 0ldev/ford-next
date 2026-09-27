import { useCallback, useEffect, useRef, useState } from "react";

export interface EstadoRequisicao<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  recarregar: () => void;
}

export function useApiResource<T>(buscar: () => Promise<T>, chave: string): EstadoRequisicao<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [tentativa, setTentativa] = useState(0);

  const buscarRef = useRef(buscar);
  useEffect(() => {
    buscarRef.current = buscar;
  });

  const chaveCompleta = `${chave}|${tentativa}`;
  const [chaveAnterior, setChaveAnterior] = useState(chaveCompleta);
  if (chaveAnterior !== chaveCompleta) {
    setChaveAnterior(chaveCompleta);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    let cancelado = false;

    buscarRef
      .current()
      .then((resultado) => {
        if (cancelado) return;
        setData(resultado);
      })
      .catch((erro: unknown) => {
        if (cancelado) return;
        setData(null);
        setError(erro instanceof Error ? erro : new Error(String(erro)));
      })
      .finally(() => {
        if (cancelado) return;
        setLoading(false);
      });

    return () => {
      cancelado = true;
    };
  }, [chave, tentativa]);

  const recarregar = useCallback(() => {
    setTentativa((valor) => valor + 1);
  }, []);

  return { data, loading, error, recarregar };
}
