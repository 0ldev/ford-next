import type { Lead } from "./types";

/**
 * O lead de maior prioridade de uma lista, ou `undefined` se ela estiver vazia.
 *
 * Compartilhado entre a tabela de leads e o card de "ação prioritária" dos
 * indicadores — os dois precisam do mesmo critério de "caso mais urgente".
 * Usa `prioridade` (risco + valor do cliente), não `score` sozinho: um VIN de
 * risco alto sem histórico de retorno não deveria ofuscar um cliente fiel.
 */
export function encontrarLeadPrioritario(leads: Lead[]): Lead | undefined {
  return leads.reduce<Lead | undefined>(
    (maior, lead) => (!maior || lead.prioridade > maior.prioridade ? lead : maior),
    undefined
  );
}
