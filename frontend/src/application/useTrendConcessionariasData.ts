import type { TrendConcessionariaFiltros, TrendConcessionariaResponse } from "../domain/types";
import { buscarTrendConcessionarias } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/**
 * Série temporal de VIN Share, uma série por concessionária.
 *
 * `concessionaria` vazio ou ausente significa "todas" — usado pelo ranking, que
 * busca a rede inteira e recorta o top N no próprio componente.
 */
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
