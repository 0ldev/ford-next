import type { TrendResponse } from "../domain/types";
import type { PontoGraficoLinha } from "./components/charts/LinhaTendenciaChart";

export function pivotarPorMes(pontos: TrendResponse): PontoGraficoLinha[] {
  const porMes = new Map<string, PontoGraficoLinha>();

  for (const ponto of pontos) {
    const linha = porMes.get(ponto.data) ?? { data: ponto.data };
    linha[ponto.categoria] = ponto.valor;
    porMes.set(ponto.data, linha);
  }

  return [...porMes.values()].sort((a, b) => a.data.localeCompare(b.data));
}
