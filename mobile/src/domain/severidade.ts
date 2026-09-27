export const LIMIAR_ALTO = 0.7;
export const LIMIAR_MEDIO = 0.3;

export type NivelRisco = "alto" | "medio" | "baixo";

export function nivelDeRisco(valor: number): NivelRisco {
  if (valor >= LIMIAR_ALTO) return "alto";
  if (valor >= LIMIAR_MEDIO) return "medio";
  return "baixo";
}
