import type { AcaoTipo } from "../domain/types";

export const ROTULO_ACAO: Record<AcaoTipo, string> = {
  contato_ativo: "Contato ativo",
  oferta: "Oferta dirigida",
  lembrete: "Lembrete automático"
};

export const COR_ACAO: Record<AcaoTipo, string> = {
  contato_ativo: "#b3261e",
  oferta: "#a35a00",
  lembrete: "#066fef"
};
