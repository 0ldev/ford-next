import type { AnomaliesResponse } from "../domain/types";
import { buscarAnomalies } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/**
 * Anomalias detectadas na rede (quedas por concessionária, gaps por modelo
 * e picos de origem fora da rede oficial).
 *
 * O endpoint não recebe filtros: o painel mostra sempre o quadro completo,
 * já ordenado por severidade pela fonte de dados.
 */
export function useAnomaliesData(): EstadoRequisicao<AnomaliesResponse> {
  return useApiResource<AnomaliesResponse>(() => buscarAnomalies(), "anomalies");
}
