import { useEffect } from "react";
import { useAcoesRecomendadas } from "../application/useAcoesRecomendadas";
import { useLeads } from "../application/useLeads";
import { encontrarLeadPrioritario } from "../domain/leads";
import KpiCard from "./KpiCard";
import { ROTULO_ACAO } from "./rotulos";

export interface AcaoPrioritariaKpiCardProps {
  /** Mesmo recorte de concessionária da tabela de leads. */
  concessionaria?: string;
}

/**
 * Indicador com a ação recomendada para o lead de maior score do recorte
 * ativo — a versão condensada (título + uma linha) do painel `AcaoPrioritaria`,
 * que continua na seção de leads com a mensagem inteira e o botão de copiar.
 */
export default function AcaoPrioritariaKpiCard({ concessionaria }: AcaoPrioritariaKpiCardProps) {
  const {
    data: paginaLeads,
    loading: carregandoLeads,
    error: erroLeads,
    recarregar: recarregarLeads
  } = useLeads({ concessionaria });
  const { acoes, carregar, recarregar } = useAcoesRecomendadas();

  const leads = paginaLeads?.leads;
  const leadPrioritario = leads ? encontrarLeadPrioritario(leads) : undefined;
  const vin = leadPrioritario?.vin;

  useEffect(() => {
    if (vin) carregar(vin);
  }, [vin, carregar]);

  const acao = vin ? acoes[vin] : undefined;

  const carregando = carregandoLeads || (Boolean(vin) && (!acao || acao.loading));
  const erro = erroLeads?.message ?? acao?.error?.message ?? null;
  const tentarNovamente = erroLeads ? recarregarLeads : vin ? () => recarregar(vin) : undefined;

  const percentual = leadPrioritario ? Math.round(leadPrioritario.score * 100) : null;
  const identificador = leadPrioritario ? leadPrioritario.vin.slice(0, 8).toUpperCase() : null;

  const valorTexto = !leadPrioritario
    ? (leads ? "Nenhum lead no recorte" : undefined)
    : acao?.data
      ? ROTULO_ACAO[acao.data.acao]
      : undefined;

  const contexto =
    leadPrioritario && percentual !== null
      ? `${leadPrioritario.modelo} · VIN ${identificador} · ${percentual}% de risco`
      : undefined;

  return (
    <KpiCard
      label="Ação prioritária"
      valorTexto={valorTexto}
      contexto={contexto}
      loading={carregando}
      erro={erro}
      onTentarNovamente={tentarNovamente}
    />
  );
}
