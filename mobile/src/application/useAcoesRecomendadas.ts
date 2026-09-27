import { useCallback, useRef, useState } from "react";
import type { AcaoRecomendada } from "../domain/types";
import { buscarAcaoRecomendada } from "../infrastructure/dataSource";

export interface EstadoAcao {
  loading: boolean;
  data: AcaoRecomendada | null;
  error: Error | null;
}

export interface AcoesRecomendadas {
  acoes: Record<string, EstadoAcao>;
  carregar: (vin: string) => void;
  recarregar: (vin: string) => void;
}

export function useAcoesRecomendadas(): AcoesRecomendadas {
  const [acoes, setAcoes] = useState<Record<string, EstadoAcao>>({});
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
          [vin]: { loading: false, data: null, error: erro instanceof Error ? erro : new Error(String(erro)) }
        }));
      });
  }, []);

  const carregar = useCallback(
    (vin: string) => {
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
