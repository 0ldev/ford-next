import { nivelDeRisco, type NivelRisco } from "../domain/severidade";
import type { Anomaly, VinShareFiltros } from "../domain/types";
import { CONCESSIONARIAS, MODELOS } from "../infrastructure/mockData";

export interface AnomaliaItemProps {
  anomalia: Anomaly;
  /** Aplica o recorte da anomalia nos filtros da página. */
  onFiltrar: (filtro: Partial<VinShareFiltros>) => void;
}

const ROTULO_NIVEL: Record<NivelRisco, string> = {
  alto: "Severidade alta",
  medio: "Severidade média",
  baixo: "Severidade baixa"
};

/** "34.7" vira "34,7%" — mesma formatação pt-BR do resto do dashboard. */
function formatarPercentual(valor: number): string {
  return `${valor.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

export interface AtalhoDeFiltro {
  filtro: Partial<VinShareFiltros>;
  rotulo: string;
}

/**
 * Traduz a entidade da anomalia para um filtro do dashboard.
 *
 * `entidade` é o nome de uma concessionária ou de um modelo, e o `tipo` não
 * distingue os dois (um pico de origem pode ser de qualquer um), então a
 * resolução é por correspondência com as mesmas listas que alimentam a barra
 * de filtros. Sem correspondência, não oferecemos o atalho — melhor não ter
 * o botão do que ter um botão que não filtra nada.
 */
export function atalhoDaAnomalia(anomalia: Anomaly): AtalhoDeFiltro | null {
  const concessionaria = CONCESSIONARIAS.find((item) => item.nome === anomalia.entidade);
  if (concessionaria) {
    return {
      filtro: { concessionaria: concessionaria.dealerCode },
      rotulo: "Ver esta concessionária"
    };
  }

  const modelo = MODELOS.find((item) => item === anomalia.entidade);
  if (modelo) {
    return { filtro: { modelo }, rotulo: "Ver este modelo" };
  }

  return null;
}

/**
 * Uma anomalia da lista.
 *
 * A severidade aparece de três formas redundantes — cor, comprimento da
 * barra e percentual escrito — para não depender só de cor: em impressão
 * preto e branco ou para quem não distingue as cores, a barra e o número
 * seguem legíveis.
 *
 * Os limiares vêm de `domain/severidade` para casar com os da tabela de
 * leads, que usa a mesma escala de cores.
 */
export default function AnomaliaItem({ anomalia, onFiltrar }: AnomaliaItemProps) {
  const nivel = nivelDeRisco(anomalia.severidade);
  const percentual = Math.round(anomalia.severidade * 100);
  const atalho = atalhoDaAnomalia(anomalia);

  /*
   * Seta de tendência derivada dos próprios valores (não fixa em "queda"):
   * gap_modelo e queda_dealer caem (atual < referência), mas pico_mainsource
   * é um aumento (atual > referência) — a direção real evita afirmar "queda"
   * onde na verdade houve alta.
   */
  const emAlta = anomalia.valorAtual > anomalia.valorReferencia;

  return (
    <li className={`anomalia anomalia-${nivel}`}>
      <div className="anomalia-cabecalho">
        <span className="anomalia-entidade">{anomalia.entidade}</span>
        <span className={`anomalia-selo anomalia-selo-${nivel}`}>
          {ROTULO_NIVEL[nivel]} · {percentual}%
        </span>
      </div>

      <p className="anomalia-resumo">
        <span className="anomalia-seta-tendencia" aria-hidden="true">
          {emAlta ? "▲" : "▼"}
        </span>{" "}
        {anomalia.resumo}
      </p>

      <p className="anomalia-comparacao">
        <span className="anomalia-comparacao-referencia">
          {formatarPercentual(anomalia.valorReferencia)}
        </span>
        <span className="anomalia-comparacao-seta" aria-hidden="true">
          →
        </span>
        <span className="anomalia-comparacao-atual">{formatarPercentual(anomalia.valorAtual)}</span>
      </p>

      <div
        className="anomalia-barra"
        role="meter"
        aria-valuenow={percentual}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Severidade de ${anomalia.entidade}`}
      >
        <div className="anomalia-barra-preenchida" style={{ width: `${percentual}%` }} />
      </div>

      {atalho && (
        <button
          type="button"
          className="botao-link anomalia-atalho"
          onClick={() => onFiltrar(atalho.filtro)}
        >
          {atalho.rotulo}
          <span className="sr-only"> — filtra o dashboard inteiro por {anomalia.entidade}</span>
        </button>
      )}
    </li>
  );
}
