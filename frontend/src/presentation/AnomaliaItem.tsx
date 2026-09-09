import type { Anomaly } from "../domain/types";

export interface AnomaliaItemProps {
  anomalia: Anomaly;
}

export type FaixaSeveridade = "alta" | "media" | "baixa";

/** Faixas usadas para colorir o item; o número exato aparece no rótulo. */
export function faixaDaSeveridade(severidade: number): FaixaSeveridade {
  if (severidade >= 0.7) return "alta";
  if (severidade >= 0.4) return "media";
  return "baixa";
}

const ROTULO_FAIXA: Record<FaixaSeveridade, string> = {
  alta: "Severidade alta",
  media: "Severidade média",
  baixa: "Severidade baixa"
};

/**
 * Uma anomalia da lista.
 *
 * A severidade aparece de três formas redundantes — cor, comprimento da
 * barra e percentual escrito — para não depender só de cor: em impressão
 * preto e branco ou para quem não distingue as cores, a barra e o número
 * seguem legíveis.
 */
export default function AnomaliaItem({ anomalia }: AnomaliaItemProps) {
  const faixa = faixaDaSeveridade(anomalia.severidade);
  const percentual = Math.round(anomalia.severidade * 100);

  return (
    <li className={`anomalia anomalia-${faixa}`}>
      <div className="anomalia-cabecalho">
        <span className="anomalia-entidade">{anomalia.entidade}</span>
        <span className={`anomalia-selo anomalia-selo-${faixa}`}>
          {ROTULO_FAIXA[faixa]} · {percentual}%
        </span>
      </div>

      <p className="anomalia-descricao">{anomalia.descricao}</p>

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
    </li>
  );
}
