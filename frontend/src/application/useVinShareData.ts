import type { VinShareFiltros, VinShareResponse } from "../domain/types";
import { buscarVinShare } from "../infrastructure/dataSource";
import { useApiResource, type EstadoRequisicao } from "./useApiResource";

/** Identidade estável dos filtros: muda quando (e só quando) o conteúdo muda. */
function chaveDosFiltros(filtros: VinShareFiltros): string {
  return JSON.stringify([
    filtros.concessionaria ?? null,
    filtros.modelo ?? null,
    filtros.faixaIdade ?? null,
    filtros.tipoServico ?? null,
    filtros.periodoInicio ?? null,
    filtros.periodoFim ?? null
  ]);
}

/**
 * KPI principal do dashboard (VIN Share estimado) para os filtros correntes.
 *
 * Refaz a busca sempre que qualquer filtro muda. A comparação é por conteúdo,
 * não por identidade do objeto, então o componente pode passar um literal
 * (`useVinShareData({ modelo })`) sem provocar loop de requisições.
 */
export function useVinShareData(filtros: VinShareFiltros = {}): EstadoRequisicao<VinShareResponse> {
  return useApiResource<VinShareResponse>(
    () => buscarVinShare(filtros),
    chaveDosFiltros(filtros)
  );
}
