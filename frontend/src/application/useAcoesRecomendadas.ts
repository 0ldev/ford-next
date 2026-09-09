import { useCallback, useRef, useState } from "react";
import type { AcaoRecomendada } from "../domain/types";
import { ApiError, toApiError } from "../infrastructure/apiClient";
import { buscarAcaoRecomendada } from "../infrastructure/dataSource";

export interface EstadoAcao {
  loading: boolean;
  data: AcaoRecomendada | null;
  error: ApiError | null;
}

export interface AcoesRecomendadas {
  /** Estado por VIN; ausente significa "ainda não pedimos". */
  acoes: Record<string, EstadoAcao>;
  /** Busca a ação do VIN, a menos que ela já esteja em cache ou em voo. */
  carregar: (vin: string) => void;
  /** Refaz a busca de um VIN ignorando o cache (botão de nova tentativa). */
  recarregar: (vin: string) => void;
}

/**
 * Ações recomendadas buscadas sob demanda, uma por VIN.
 *
 * O endpoint é por veículo, então pré-carregar a tabela inteira custaria 50
 * requisições para uma informação que o gestor abre em duas ou três linhas.
 * O resultado fica em cache: recolher e reabrir a mesma linha não gera nova
 * chamada.
 */
export function useAcoesRecomendadas(): AcoesRecomendadas {
  const [acoes, setAcoes] = useState<Record<string, EstadoAcao>>({});
  // Fora do estado: o StrictMode invoca o corpo do componente duas vezes, e
  // um Set em ref garante uma requisição por VIN mesmo assim.
  const solicitados = useRef(new Set<string>());

  const buscar = useCallback((vin: string) => {
    setAcoes((atual) => ({
      ...atual,
      [vin]: { loading: true, data: null, error: null }
    }));

    buscarAcaoRecomendada(vin)
      .then((data) => {
        setAcoes((atual) => ({ ...atual, [vin]: { loading: false, data, error: null } }));
      })
      .catch((erro: unknown) => {
        setAcoes((atual) => ({
          ...atual,
          [vin]: { loading: false, data: null, error: toApiError(erro) }
        }));
      });
  }, []);

  const carregar = useCallback(
    (vin: string) => {
      // Já carregado, carregando ou em erro: quem decide repetir é o retry.
      if (solicitados.current.has(vin)) return;
      solicitados.current.add(vin);
      buscar(vin);
    },
    [buscar]
  );

  const recarregar = useCallback(
    (vin: string) => {
      solicitados.current.add(vin);
      buscar(vin);
    },
    [buscar]
  );

  return { acoes, carregar, recarregar };
}
