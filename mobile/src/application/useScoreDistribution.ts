import type { ScoreDistributionResponse } from "../domain/types";
import { buscarDistribuicaoScore } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

export function useScoreDistribution(): EstadoRequisicao<ScoreDistributionResponse> {
  return useApiResource<ScoreDistributionResponse>(() => buscarDistribuicaoScore(), "score-distribution");
}
