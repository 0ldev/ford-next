import type { AcaoTipo } from "../domain/types";

/**
 * Nome de exibição de cada ação recomendada.
 *
 * Vive num módulo próprio porque a tabela de leads e o card de ação
 * prioritária precisam do mesmo rótulo, e o card é renderizado de dentro da
 * tabela — importar um do outro criaria um ciclo.
 */
export const ROTULO_ACAO: Record<AcaoTipo, string> = {
  contato_ativo: "Contato ativo",
  oferta: "Oferta dirigida",
  lembrete: "Lembrete automático"
};
