import type { AnomaliesResponse } from "../domain/types";
import { buscarAnomalies } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

export function useAnomaliesData(): EstadoRequisicao<AnomaliesResponse> {
  return useApiResource<AnomaliesResponse>(() => buscarAnomalies(), "anomalies");
}
