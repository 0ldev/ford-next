import type { Catalogo } from "../domain/types";
import { buscarCatalogo } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

export function useCatalogo(): EstadoRequisicao<Catalogo> {
  return useApiResource<Catalogo>(() => buscarCatalogo(), "catalogo");
}
