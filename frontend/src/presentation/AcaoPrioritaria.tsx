import { useEffect } from "react";
import type { EstadoAcao } from "../application/useAcoesRecomendadas";
import { nivelDeRisco } from "../domain/severidade";
import type { Lead } from "../domain/types";
import BotaoCopiar from "./BotaoCopiar";
import EstadoErro from "./EstadoErro";
import { ROTULO_ACAO } from "./rotulos";

export interface AcaoPrioritariaProps {
  /** Lead de maior score do recorte ativo; ausente quando a fila está vazia. */
  lead?: Lead;
  /** Nome de exibição da concessionária do lead. */
  concessionaria: string;
  /** Estado da ação no cache compartilhado com a tabela. */
  acao?: EstadoAcao;
  /** Pede a ação ao hook; ignorado se o VIN já estiver em cache. */
  onCarregar: (vin: string) => void;
  onTentarNovamente: (vin: string) => void;
}

/**
 * O caso mais urgente do recorte, com a ação já resolvida.
 *
 * É a tradução de "insight vira ação" numa peça só: risco, motivo e o que
 * fazer a respeito, sem exigir que alguém expanda uma linha da tabela para
 * descobrir. Usa o mesmo cache da tabela, então abrir depois a linha desse
 * mesmo veículo não custa nova busca.
 */
export default function AcaoPrioritaria({
  lead,
  concessionaria,
  acao,
  onCarregar,
  onTentarNovamente
}: AcaoPrioritariaProps) {
  const vin = lead?.vin;

  useEffect(() => {
    if (vin) onCarregar(vin);
  }, [vin, onCarregar]);

  if (!lead) return null;

  const nivel = nivelDeRisco(lead.score);
  const percentual = Math.round(lead.score * 100);

  return (
    <aside className="acao-prioritaria" aria-labelledby="acao-prioritaria-titulo">
      <div className="acao-prioritaria-topo">
        <h3 className="acao-prioritaria-titulo" id="acao-prioritaria-titulo">
          Ação prioritária agora
        </h3>
        <span className={`score score-${nivel}`}>{percentual}% de risco</span>
      </div>

      <p className="acao-prioritaria-veiculo">
        <strong>{lead.modelo}</strong>
        <span className="acao-prioritaria-vin" title={lead.vin}>
          VIN {lead.vin.slice(0, 8).toUpperCase()}
        </span>
        <span className="acao-prioritaria-dealer">{concessionaria}</span>
      </p>

      <p className="acao-prioritaria-motivo">{lead.motivo}</p>

      {!acao || acao.loading ? (
        <p className="placeholder-texto" role="status">
          Buscando ação recomendada…
        </p>
      ) : acao.error ? (
        <EstadoErro
          mensagem={acao.error.message}
          onTentarNovamente={() => onTentarNovamente(lead.vin)}
        />
      ) : acao.data ? (
        <div className="acao-prioritaria-acao">
          <span className={`selo-acao selo-acao-${acao.data.acao}`}>
            {ROTULO_ACAO[acao.data.acao]}
          </span>
          <p className="detalhe-mensagem">{acao.data.mensagem}</p>
          <BotaoCopiar texto={acao.data.mensagem} />
        </div>
      ) : null}
    </aside>
  );
}
