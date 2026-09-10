/**
 * Limiares de risco compartilhados pela tela inteira.
 *
 * O painel de anomalias e a tabela de leads usam a mesma linguagem visual
 * (alto/médio/baixo, com as mesmas cores), então precisam do mesmo corte.
 * Antes as anomalias cortavam "médio" em 0,4 e os leads em 0,3: um valor de
 * 0,35 aparecia cinza num painel e âmbar no outro.
 */

/** A partir daqui, risco alto. */
export const LIMIAR_ALTO = 0.7;

/** A partir daqui, risco médio; abaixo, baixo. */
export const LIMIAR_MEDIO = 0.3;

export type NivelRisco = "alto" | "medio" | "baixo";

/**
 * Classifica um valor de 0 a 1 — serve tanto para a severidade de uma
 * anomalia quanto para o score de evasão de um lead.
 */
export function nivelDeRisco(valor: number): NivelRisco {
  if (valor >= LIMIAR_ALTO) return "alto";
  if (valor >= LIMIAR_MEDIO) return "medio";
  return "baixo";
}
