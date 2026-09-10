import { nivelDeRisco, type NivelRisco } from "../domain/severidade";
import type { Anomaly } from "../domain/types";

export interface AnomaliaItemProps {
  anomalia: Anomaly;
}

const ROTULO_NIVEL: Record<NivelRisco, string> = {
  alto: "Severidade alta",
  medio: "Severidade média",
  baixo: "Severidade baixa"
};

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
export default function AnomaliaItem({ anomalia }: AnomaliaItemProps) {
  const nivel = nivelDeRisco(anomalia.severidade);
  const percentual = Math.round(anomalia.severidade * 100);

  return (
    <li className={`anomalia anomalia-${nivel}`}>
      <div className="anomalia-cabecalho">
        <span className="anomalia-entidade">{anomalia.entidade}</span>
        <span className={`anomalia-selo anomalia-selo-${nivel}`}>
          {ROTULO_NIVEL[nivel]} · {percentual}%
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
