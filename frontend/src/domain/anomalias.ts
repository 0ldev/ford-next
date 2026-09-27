import type { AnomalyTipo } from "./types";

/**
 * O que `entidade` representa em cada tipo de anomalia — sem isso, o card mostra
 * só o código cru (ex.: "3127") e quem lê não sabe se é uma concessionária, um
 * modelo, ou o quê. Ver `application.anomaly_detection` (backend): `entidade` é o
 * `DealerCode` para `queda_dealer`/`pico_mainsource`, ou o `ModelName` para
 * `gap_modelo`.
 */
const ROTULO_TIPO_ENTIDADE: Record<AnomalyTipo, string> = {
  queda_dealer: "Concessionária",
  gap_modelo: "Modelo",
  pico_mainsource: "Concessionária"
};

/** "3127" (tipo `pico_mainsource`) vira "Concessionária 3127". */
export function rotularEntidadeDaAnomalia(tipo: AnomalyTipo, entidade: string): string {
  return `${ROTULO_TIPO_ENTIDADE[tipo]} ${entidade}`;
}
