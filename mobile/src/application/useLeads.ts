import type { LeadsFiltros, LeadsResponse } from "../domain/types";
import { buscarLeads } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

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
