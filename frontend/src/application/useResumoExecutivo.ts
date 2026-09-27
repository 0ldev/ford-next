import type { ResumoExecutivo } from "../domain/types";
import { buscarResumoExecutivo } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/**
 * As três listas do resumo executivo (concessionárias em alerta, modelos com
 * maior risco, meses com maior evasão aparente) — sem filtros, sempre o
 * recorte de rede inteira, já ordenado por prioridade pela fonte de dados.
 */
export function useResumoExecutivo(): EstadoRequisicao<ResumoExecutivo> {
  return useApiResource<ResumoExecutivo>(() => buscarResumoExecutivo(), "resumo-executivo");
}
