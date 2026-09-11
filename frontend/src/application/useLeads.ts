import type { LeadsFiltros, LeadsResponse } from "../domain/types";
import { buscarLeads } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/**
 * Página de leads priorizada, opcionalmente restrita a uma concessionária e/ou
 * a um piso de score. Sem filtro, devolve a primeira página da fila consolidada
 * da rede.
 *
 * Os leads já chegam ordenados por score decrescente da fonte de dados;
 * a ordenação dentro da página é responsabilidade do componente.
 */
export function useLeads(filtros: LeadsFiltros = {}): EstadoRequisicao<LeadsResponse> {
  const chave = JSON.stringify([
    filtros.concessionaria ?? null,
    filtros.scoreMinimo ?? null,
    filtros.scoreMaximo ?? null,
    filtros.pagina ?? null,
    filtros.tamanhoPagina ?? null
  ]);

  return useApiResource<LeadsResponse>(() => buscarLeads(filtros), chave);
}
