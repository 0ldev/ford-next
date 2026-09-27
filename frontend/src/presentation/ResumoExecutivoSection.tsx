import type { ReactNode } from "react";
import { useResumoExecutivo } from "../application/useResumoExecutivo";
import { rotularEntidadeDaAnomalia } from "../domain/anomalias";
import { formatarCompetenciaLonga } from "../domain/competencia";
import { nivelDeRisco } from "../domain/severidade";
import type { ConcessionariaEmAlerta, MesMaiorChurn, ModeloMaiorRisco } from "../domain/types";
import EstadoErro from "./EstadoErro";

/** "2024-06" vira "Junho/2024" — mais curto que `formatarCompetenciaLonga` para caber no card. */
function formatarMesCurto(competencia: string): string {
  const longa = formatarCompetenciaLonga(competencia); // "junho de 2024"
  const [mes, , ano] = longa.split(" ");
  if (!mes || !ano) return competencia;
  return `${mes[0].toUpperCase()}${mes.slice(1)}/${ano}`;
}

interface LinhaResumoProps {
  rank: number;
  titulo: string;
  legenda: string;
  valor: string;
  nivel?: "alto" | "medio" | "baixo";
}

function LinhaResumo({ rank, titulo, legenda, valor, nivel }: LinhaResumoProps) {
  return (
    <li className="resumo-linha">
      <span className="resumo-rank" aria-hidden="true">
        {rank}
      </span>
      <div className="resumo-linha-corpo">
        <span className="resumo-linha-titulo">{titulo}</span>
        <span className="resumo-linha-legenda" title={legenda}>
          {legenda}
        </span>
      </div>
      <span className={`resumo-linha-valor${nivel ? ` score-${nivel}` : ""}`}>{valor}</span>
    </li>
  );
}

function CardResumo({
  titulo,
  vazio,
  children
}: {
  titulo: string;
  vazio: boolean;
  children: ReactNode;
}) {
  return (
    <section className="resumo-card">
      <h3 className="resumo-card-titulo">{titulo}</h3>
      {vazio ? (
        <p className="lista-vazia">Nenhum destaque no momento.</p>
      ) : (
        <ol className="resumo-lista">{children}</ol>
      )}
    </section>
  );
}

/**
 * Resumo executivo: as três listas de "onde agir primeiro", pensadas para
 * ler em segundos — cada linha é um número grande e uma legenda de uma linha
 * só, sem parágrafo. Complementa o painel de anomalias (que tem o detalhe
 * completo); este aqui é só o atalho visual pro topo do problema.
 */
export default function ResumoExecutivoSection() {
  const { data, loading, error, recarregar } = useResumoExecutivo();

  if (error) {
    return (
      <div className="painel-estado">
        <EstadoErro mensagem={error.message} onTentarNovamente={recarregar} />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="painel-estado" role="status">
        <p className="placeholder-texto">Carregando resumo executivo…</p>
      </div>
    );
  }

  const concessionarias: ConcessionariaEmAlerta[] = data?.concessionariasEmAlerta ?? [];
  const modelos: ModeloMaiorRisco[] = data?.modelosMaiorRisco ?? [];
  const meses: MesMaiorChurn[] = data?.mesesMaiorChurn ?? [];

  return (
    <div className="resumo-executivo">
      <div className="resumo-grade">
        <CardResumo titulo="Concessionárias em alerta" vazio={concessionarias.length === 0}>
          {concessionarias.map((item, indice) => (
            <LinhaResumo
              key={item.dealerCode}
              rank={indice + 1}
              titulo={rotularEntidadeDaAnomalia(item.tipo, item.dealerCode)}
              legenda={item.resumo}
              valor={`${Math.round(item.severidade * 100)}%`}
              nivel={nivelDeRisco(item.severidade)}
            />
          ))}
        </CardResumo>

        <CardResumo titulo="Modelos com maior risco" vazio={modelos.length === 0}>
          {modelos.map((item, indice) => (
            <LinhaResumo
              key={item.modelo}
              rank={indice + 1}
              titulo={item.modelo}
              legenda={`${item.totalVeiculos.toLocaleString("pt-BR")} veículos · verificar motivos`}
              valor={`${Math.round(item.percentualAltoRisco)}%`}
              nivel={nivelDeRisco(item.percentualAltoRisco / 100)}
            />
          ))}
        </CardResumo>

        <CardResumo titulo="Meses com maior evasão" vazio={meses.length === 0}>
          {meses.map((item, indice) => (
            <LinhaResumo
              key={item.competencia}
              rank={indice + 1}
              titulo={formatarMesCurto(item.competencia)}
              legenda="VIN Share da rede"
              valor={`${Math.round(item.vinShareRede)}%`}
            />
          ))}
        </CardResumo>
      </div>
    </div>
  );
}
