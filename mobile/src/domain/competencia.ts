import type { TrendResponse } from "./types";

export function competenciaDeReferencia(pontos: TrendResponse): string | undefined {
  const totalPorMes = new Map<string, number>();
  for (const ponto of pontos) {
    totalPorMes.set(ponto.data, (totalPorMes.get(ponto.data) ?? 0) + ponto.valor);
  }

  const meses = [...totalPorMes.keys()].sort();
  if (meses.length === 0) return undefined;

  const ultimo = meses[meses.length - 1];
  if (meses.length >= 4) {
    const totalUltimo = totalPorMes.get(ultimo) ?? 0;
    const anteriores = meses.slice(-4, -1).map((mes) => totalPorMes.get(mes) ?? 0);
    const mediaAnteriores = anteriores.reduce((soma, valor) => soma + valor, 0) / anteriores.length;

    if (mediaAnteriores > 0 && totalUltimo < mediaAnteriores / 2) {
      return meses[meses.length - 2];
    }
  }

  return ultimo;
}

const MESES_LONGOS = [
  "janeiro",
  "fevereiro",
  "março",
  "abril",
  "maio",
  "junho",
  "julho",
  "agosto",
  "setembro",
  "outubro",
  "novembro",
  "dezembro"
];

const MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

export function formatarCompetenciaLonga(competencia: string): string {
  const [ano, mes] = competencia.split("-");
  const indice = Number(mes) - 1;
  if (!ano || Number.isNaN(indice) || !MESES_LONGOS[indice]) return competencia;
  return `${MESES_LONGOS[indice]} de ${ano}`;
}

export function formatarCompetencia(competencia: string): string {
  const [ano, mes] = competencia.split("-");
  const indice = Number(mes) - 1;
  if (!ano || Number.isNaN(indice) || !MESES_CURTOS[indice]) return competencia;
  return `${MESES_CURTOS[indice]}/${ano.slice(2)}`;
}

export function formatarCompetenciaCurtaMes(competencia: string): string {
  const [, mes] = competencia.split("-");
  const indice = Number(mes) - 1;
  return MESES_CURTOS[indice] ?? competencia;
}
