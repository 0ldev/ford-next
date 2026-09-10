import type { VinShareFiltros } from "../domain/types";
import { CONCESSIONARIAS, FAIXAS_IDADE } from "../infrastructure/mockData";

export interface ResumoFiltrosProps {
  filtros: VinShareFiltros;
}

/**
 * Formata "2025-01-31" como "31/01/2025".
 *
 * Feito por recorte de string de propósito: `new Date("2025-01-31")` é lido
 * como UTC e, no fuso do Brasil, voltaria um dia na exibição.
 */
export function formatarDataBR(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : iso;
}

function rotuloDaConcessionaria(dealerCode: string): string {
  return CONCESSIONARIAS.find((item) => item.dealerCode === dealerCode)?.nome ?? dealerCode;
}

function rotuloDaFaixa(valor: string): string {
  return FAIXAS_IDADE.find((faixa) => faixa.value === valor)?.label ?? valor;
}

function trechoDePeriodo(inicio?: string, fim?: string): string | null {
  if (inicio && fim) return `de ${formatarDataBR(inicio)} a ${formatarDataBR(fim)}`;
  if (inicio) return `a partir de ${formatarDataBR(inicio)}`;
  if (fim) return `até ${formatarDataBR(fim)}`;
  return null;
}

/** Monta a lista em português: "a, b e c". */
function juntar(trechos: string[]): string {
  if (trechos.length === 1) return trechos[0];
  return `${trechos.slice(0, -1).join(", ")} e ${trechos[trechos.length - 1]}`;
}

/** Descreve o recorte ativo em uma frase. Exportada para teste. */
export function descreverFiltros(filtros: VinShareFiltros): string {
  const trechos: string[] = [];

  if (filtros.concessionaria) {
    trechos.push(`concessionária ${rotuloDaConcessionaria(filtros.concessionaria)}`);
  }
  if (filtros.modelo) trechos.push(`modelo ${filtros.modelo}`);
  if (filtros.faixaIdade) trechos.push(`veículos de ${rotuloDaFaixa(filtros.faixaIdade)}`);
  if (filtros.tipoServico) trechos.push(`serviços de ${filtros.tipoServico.toLowerCase()}`);

  const periodo = trechoDePeriodo(filtros.periodoInicio, filtros.periodoFim);
  if (periodo) trechos.push(periodo);

  if (trechos.length === 0) return "todos os veículos elegíveis da rede, em todo o período";

  return juntar(trechos);
}

/**
 * Traduz os filtros ativos para uma frase.
 *
 * Numa demonstração ao vivo, quem assiste não acompanha seis dropdowns ao
 * mesmo tempo; esta linha diz em voz alta de que recorte a tela está
 * falando. Não busca nada: deriva do mesmo estado que já move o dashboard.
 */
export default function ResumoFiltros({ filtros }: ResumoFiltrosProps) {
  return (
    <p className="resumo-filtros" aria-live="polite">
      <span className="resumo-filtros-rotulo">Mostrando</span>
      {descreverFiltros(filtros)}
    </p>
  );
}
