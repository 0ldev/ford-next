import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { Catalogo, VinShareFiltros } from "../domain/types";
import { useCatalogo } from "./useCatalogo";

function limparVazios(filtros: VinShareFiltros): VinShareFiltros {
  const resultado: VinShareFiltros = {};
  for (const [chave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== "") {
      resultado[chave as keyof VinShareFiltros] = valor;
    }
  }
  return resultado;
}

interface FiltrosContextValue {
  filtros: VinShareFiltros;
  atualizarFiltros: (alteracao: Partial<VinShareFiltros>) => void;
  limparFiltros: () => void;
  catalogo: Catalogo | null;
  catalogoCarregando: boolean;
}

const FiltrosContext = createContext<FiltrosContextValue | null>(null);

export function FiltrosProvider({ children }: { children: ReactNode }) {
  const [filtros, setFiltros] = useState<VinShareFiltros>({});
  const { data: catalogo, loading: catalogoCarregando } = useCatalogo();

  const periodoPadraoAplicado = useRef(false);
  useEffect(() => {
    if (periodoPadraoAplicado.current || !catalogo?.periodoDisponivel) return;
    periodoPadraoAplicado.current = true;

    setFiltros((atual) =>
      atual.periodoInicio || atual.periodoFim
        ? atual
        : {
            ...atual,
            periodoInicio: catalogo.periodoDisponivel!.inicio,
            periodoFim: catalogo.periodoDisponivel!.fim
          }
    );
  }, [catalogo]);

  const atualizarFiltros = useCallback((alteracao: Partial<VinShareFiltros>) => {
    setFiltros((atual) => limparVazios({ ...atual, ...alteracao }));
  }, []);

  const limparFiltros = useCallback(() => {
    setFiltros({});
  }, []);

  const valor = useMemo<FiltrosContextValue>(
    () => ({ filtros, atualizarFiltros, limparFiltros, catalogo: catalogo ?? null, catalogoCarregando }),
    [filtros, atualizarFiltros, limparFiltros, catalogo, catalogoCarregando]
  );

  return <FiltrosContext.Provider value={valor}>{children}</FiltrosContext.Provider>;
}

export function useFiltros(): FiltrosContextValue {
  const contexto = useContext(FiltrosContext);
  if (!contexto) throw new Error("useFiltros precisa estar dentro de FiltrosProvider");
  return contexto;
}
