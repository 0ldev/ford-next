import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, toApiError } from "../infrastructure/apiClient";

/**
 * Estado padrão de qualquer requisição do dashboard. Todos os hooks de dados
 * expõem exatamente esta forma, para que os componentes tratem loading e erro
 * do mesmo jeito em toda a tela.
 */
export interface EstadoRequisicao<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  /** Refaz a busca com os mesmos parâmetros (usado no botão "tentar novamente"). */
  recarregar: () => void;
}

/**
 * Base compartilhada pelos hooks de dados.
 *
 * @param buscar  função que dispara a requisição; pode ser recriada a cada render.
 * @param chave   identidade serializada dos parâmetros. Quando ela muda, a
 *                busca é refeita — é o que faz os filtros da tela funcionarem
 *                sem depender da identidade do objeto de filtros.
 */
export function useApiResource<T>(buscar: () => Promise<T>, chave: string): EstadoRequisicao<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [tentativa, setTentativa] = useState(0);

  // Mantém a versão mais recente de `buscar` sem re-disparar o efeito a cada render.
  const buscarRef = useRef(buscar);
  buscarRef.current = buscar;

  useEffect(() => {
    let cancelado = false;

    setLoading(true);
    setError(null);

    buscarRef
      .current()
      .then((resultado) => {
        // Descarta respostas de filtros já substituídos (evita race condition).
        if (cancelado) return;
        setData(resultado);
      })
      .catch((erro: unknown) => {
        if (cancelado) return;
        setData(null);
        setError(toApiError(erro));
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
