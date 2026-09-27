import type { VinShareFiltros, VinShareResponse } from "../domain/types";
import { buscarVinShare } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

export function useVinShareData(filtros: VinShareFiltros = {}): EstadoRequisicao<VinShareResponse> {
  const chave = JSON.stringify([
    filtros.concessionaria ?? null,
    filtros.modelo ?? null,
    filtros.faixaIdade ?? null,
    filtros.tipoServico ?? null,
    filtros.periodoInicio ?? null,
    filtros.periodoFim ?? null
  ]);

  return useApiResource<VinShareResponse>(() => buscarVinShare(filtros), chave);
}
