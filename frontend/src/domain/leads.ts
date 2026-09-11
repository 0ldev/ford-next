import type { Lead } from "./types";

/**
 * O lead de maior score de uma lista, ou `undefined` se ela estiver vazia.
 *
 * Compartilhado entre a tabela de leads e o card de "ação prioritária" dos
 * indicadores — os dois precisam do mesmo critério de "caso mais urgente".
 */
export function encontrarLeadPrioritario(leads: Lead[]): Lead | undefined {
  return leads.reduce<Lead | undefined>(
    (maior, lead) => (!maior || lead.score > maior.score ? lead : maior),
    undefined
  );
}
