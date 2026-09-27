import type { TrendFiltros, TrendResponse } from "../domain/types";
import { buscarTrend } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

export function useTrendData(filtros: TrendFiltros = {}): EstadoRequisicao<TrendResponse> {
  const chave = JSON.stringify([
    [...(filtros.modelo ?? [])].sort(),
    filtros.periodoInicio ?? null,
    filtros.periodoFim ?? null
  ]);

  return useApiResource<TrendResponse>(() => buscarTrend(filtros), chave);
}
