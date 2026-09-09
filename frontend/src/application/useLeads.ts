import type { LeadsFiltros, LeadsResponse } from "../domain/types";
import { buscarLeads } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/**
 * Lista de leads priorizada (top 50), opcionalmente restrita a uma
 * concessionária. Sem filtro, devolve a fila consolidada da rede.
 *
 * Os leads já chegam ordenados por score decrescente da fonte de dados;
 * a ordenação da tabela na tela é responsabilidade do componente.
 */
export function useLeads(filtros: LeadsFiltros = {}): EstadoRequisicao<LeadsResponse> {
  const chave = JSON.stringify([filtros.concessionaria ?? null]);

  return useApiResource<LeadsResponse>(() => buscarLeads(filtros), chave);
}
