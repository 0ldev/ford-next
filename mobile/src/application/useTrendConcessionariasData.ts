import type { TrendConcessionariaFiltros, TrendConcessionariaResponse } from "../domain/types";
import { buscarTrendConcessionarias } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

export function useTrendConcessionariasData(
  filtros: TrendConcessionariaFiltros = {}
): EstadoRequisicao<TrendConcessionariaResponse> {
  const chave = JSON.stringify([
    [...(filtros.concessionaria ?? [])].sort(),
    filtros.periodoInicio ?? null,
    filtros.periodoFim ?? null,
    filtros.minVeiculos ?? null
  ]);

  return useApiResource<TrendConcessionariaResponse>(() => buscarTrendConcessionarias(filtros), chave);
}
