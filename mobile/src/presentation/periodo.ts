import { listarMeses } from "../infrastructure/mockData";

export function ultimoDiaDoMes(competencia: string): string {
  const [ano, mes] = competencia.split("-").map(Number);
  const ultimoDia = new Date(ano, mes, 0).getDate();
  return `${competencia}-${String(ultimoDia).padStart(2, "0")}`;
}

export function primeiroDiaDoMes(competencia: string): string {
  return `${competencia}-01`;
}

export function competenciasDoPeriodo(inicio?: string, fim?: string): string[] {
  if (!inicio || !fim) return [];
  return listarMeses(inicio.slice(0, 7), fim.slice(0, 7));
}
