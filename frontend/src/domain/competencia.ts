import type { TrendResponse } from "./types";

/**
 * Última competência "utilizável" (não claramente truncada) presente nos pontos.
 *
 * O snapshot de um mês em andamento no momento da extração dos dados (ex.: maio de
 * 2026 tem só ~350 ordens de serviço contra ~11-12 mil num mês cheio) faz toda
 * categoria parecer perto de zero — não porque a rede piorou, mas porque o mês não
 * terminou. Mesma heurística do backend (`anomaly_detection._competencias_completas`):
 * soma o `valor` de todas as categorias por mês como proxy de volume total e descarta
 * o último mês se ele cair para menos da metade da média dos 3 anteriores.
 *
 * Compartilhada entre `VinShareModeloChart` e `VinShareConcessionariaChart` — os dois
 * precisam da mesma foto "mês mais recente com dado de verdade", só o agrupamento
 * (modelo vs. concessionária) muda.
 */
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

/** "2026-04" vira "abril de 2026". */
export function formatarCompetenciaLonga(competencia: string): string {
  const [ano, mes] = competencia.split("-");
  const indice = Number(mes) - 1;
  if (!ano || Number.isNaN(indice) || !MESES_LONGOS[indice]) return competencia;
  return `${MESES_LONGOS[indice]} de ${ano}`;
}
