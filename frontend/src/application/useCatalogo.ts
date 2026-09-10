import type { Catalogo } from "../domain/types";
import { buscarCatalogo } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/**
 * Opções reais de modelo/concessionária/tipo de serviço para os filtros do
 * dashboard. Busca uma vez só (chave constante) — o catálogo não depende de
 * nenhum filtro, então não faz sentido refazer a busca quando eles mudam.
 */
export function useCatalogo(): EstadoRequisicao<Catalogo> {
  return useApiResource<Catalogo>(() => buscarCatalogo(), "catalogo");
}
