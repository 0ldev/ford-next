import type { Lead } from "./types";

export function encontrarLeadPrioritario(leads: Lead[]): Lead | undefined {
  return leads.reduce<Lead | undefined>(
    (maior, lead) => (!maior || lead.prioridade > maior.prioridade ? lead : maior),
    undefined
  );
}
