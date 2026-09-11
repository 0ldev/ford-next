import type { ScoreDistributionResponse } from "../domain/types";
import { buscarDistribuicaoScore } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/**
 * Distribuição do score de risco na base inteira de leads (não o top 50).
 *
 * Sem filtros: é a mesma foto para qualquer recorte da página, então busca uma
 * vez só (chave constante), igual a `useAnomaliesData`.
 */
export function useScoreDistribution(): EstadoRequisicao<ScoreDistributionResponse> {
  return useApiResource<ScoreDistributionResponse>(() => buscarDistribuicaoScore(), "score-distribution");
}
