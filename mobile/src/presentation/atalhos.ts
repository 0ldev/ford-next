import type { Anomaly, VinShareFiltros } from "../domain/types";
import { CONCESSIONARIAS, MODELOS } from "../infrastructure/mockData";

export interface AtalhoDeFiltro {
  filtro: Partial<VinShareFiltros>;
  rotulo: string;
}

export function atalhoDaAnomalia(anomalia: Anomaly): AtalhoDeFiltro | null {
  const concessionaria = CONCESSIONARIAS.find((item) => item.nome === anomalia.entidade);
  if (concessionaria) {
    return { filtro: { concessionaria: concessionaria.dealerCode }, rotulo: "Ver esta concessionária" };
  }

  const modelo = MODELOS.find((item) => item === anomalia.entidade);
  if (modelo) {
    return { filtro: { modelo }, rotulo: "Ver este modelo" };
  }

  return null;
}
