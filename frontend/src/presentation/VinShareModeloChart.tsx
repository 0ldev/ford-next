import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { useTrendData } from "../application/useTrendData";
import { competenciaDeReferencia, formatarCompetenciaLonga } from "../domain/competencia";
import EstadoErro from "./EstadoErro";

export interface VinShareModeloChartProps {
  /** Recorte de período herdado dos filtros da página. */
  periodoInicio?: string;
  periodoFim?: string;
}

interface BarraModelo {
  modelo: string;
  valor: number;
}

/*
 * Cor sólida única (não vem de custom property — o SVG do Recharts recebe cor
 * por prop, igual à paleta de TrendChart). Ranking de um modelo por barra é
 * categoria nominal com uma única métrica: uma cor para todas as barras, o
 * comprimento é quem carrega a magnitude (ver skill de dataviz — colorir cada
 * barra por seu próprio valor gastaria o canal de identidade à toa).
 */
const COR_BARRA = "#00095b"; // --azul-800
const COR_CURSOR = "#eef1f8"; // --neutro-100
const COR_ROTULO = "#151a29"; // --cor-texto (--neutro-900)

const ALTURA_MINIMA = 160;
const ALTURA_POR_BARRA = 28;

/**
 * Ranking de VIN Share por modelo na competência mais recente disponível.
 *
 * Complementa o gráfico de tendência (evolução no tempo) com uma foto do
 * presente: quais modelos estão bem e quais estão atrás agora. Reaproveita o
 * mesmo GET /api/trend (sem filtro de modelo, então todos entram) — nenhuma
 * chamada nova ao backend além da que a tendência já faz.
 *
 * Modelos com `valor === 0` na competência de referência ficam de fora do
 * ranking: para os de baixo volume (ex.: 7BC, com poucas dezenas de VINs na
 * vida toda), 0% num único mês quase sempre significa "não tivemos nenhum
 * serviço desse modelo nesse mês" (sem dado), não "o modelo caiu a zero" —
 * mostrar a barra vazia sugeriria o segundo quando o real é o primeiro.
 */
export default function VinShareModeloChart({ periodoInicio, periodoFim }: VinShareModeloChartProps) {
  const { data, loading, error, recarregar } = useTrendData({ periodoInicio, periodoFim });

  const competencia = useMemo(() => (data ? competenciaDeReferencia(data) : undefined), [data]);

  const barras = useMemo<BarraModelo[]>(() => {
    if (!data || !competencia) return [];
    return data
      .filter((ponto) => ponto.data === competencia && ponto.valor > 0)
      .map((ponto) => ({ modelo: ponto.categoria, valor: ponto.valor }))
      .sort((a, b) => b.valor - a.valor);
  }, [data, competencia]);

  const valorMaximo = useMemo(
    () => Math.max(10, ...barras.map((barra) => barra.valor)),
    [barras]
  );

  const altura = Math.max(barras.length * ALTURA_POR_BARRA + 40, ALTURA_MINIMA);

  return (
    <div className="grafico">
      {error ? (
        <div className="grafico-estado">
          <EstadoErro mensagem={error.message} onTentarNovamente={recarregar} />
        </div>
      ) : loading ? (
        <div className="grafico-estado" role="status">
          <p className="placeholder-texto">Carregando ranking por modelo…</p>
        </div>
      ) : barras.length === 0 || !competencia ? (
        <div className="grafico-estado">
          <p className="placeholder-texto">Nenhum dado de VIN Share por modelo para este recorte.</p>
        </div>
      ) : (
        <>
          <p className="grafico-legenda">
            Competência de referência: <strong>{formatarCompetenciaLonga(competencia)}</strong>
          </p>
          <div className="grafico-area" style={{ height: altura }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={barras}
                layout="vertical"
                margin={{ top: 4, right: 44, bottom: 4, left: 8 }}
                barCategoryGap={6}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[0, Math.ceil(valorMaximo * 1.15)]}
                  tickFormatter={(valor: number) => `${valor}%`}
                />
                <YAxis type="category" dataKey="modelo" width={130} />
                <Tooltip
                  cursor={{ fill: COR_CURSOR }}
                  formatter={(valor: number) => [`${valor}%`, "VIN Share"]}
                  labelFormatter={(modelo: string) => modelo}
                />
                <Bar dataKey="valor" fill={COR_BARRA} radius={[0, 4, 4, 0]} maxBarSize={22}>
                  <LabelList
                    dataKey="valor"
                    position="right"
                    formatter={(valor: number) => `${valor}%`}
                    fill={COR_ROTULO}
                    fontSize={12}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
