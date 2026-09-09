import type { TrendFiltros, TrendResponse } from "../domain/types";
import { buscarTrend } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/**
 * Série temporal de VIN Share, uma série por modelo.
 *
 * `modelo` vazio ou ausente significa "todos os modelos" — é o padrão do
 * gráfico quando o usuário não marcou nenhum no seletor.
 */
export function useTrendData(filtros: TrendFiltros = {}): EstadoRequisicao<TrendResponse> {
  const chave = JSON.stringify([
    [...(filtros.modelo ?? [])].sort(),
    filtros.periodoInicio ?? null,
    filtros.periodoFim ?? null
  ]);

  return useApiResource<TrendResponse>(() => buscarTrend(filtros), chave);
}
