import { useEffect } from "react";
import { useAcoesRecomendadas } from "../../application/useAcoesRecomendadas";
import { useLeads } from "../../application/useLeads";
import { encontrarLeadPrioritario } from "../../domain/leads";
import { ROTULO_ACAO } from "../rotulos";
import KpiCard from "./KpiCard";

export interface AcaoPrioritariaKpiCardProps {
  concessionaria?: string;
}

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
    ? leads
      ? "Nenhum lead no recorte"
      : undefined
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
