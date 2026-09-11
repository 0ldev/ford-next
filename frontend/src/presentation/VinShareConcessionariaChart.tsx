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
import { useTrendConcessionariasData } from "../application/useTrendConcessionariasData";
import { competenciaDeReferencia, formatarCompetenciaLonga } from "../domain/competencia";
import { rotuloDaConcessionaria } from "../infrastructure/mockData";
import EstadoErro from "./EstadoErro";

const TOP_N = 15;

/*
 * Sem piso, dealers de 1-2 VINs elegíveis entopem o topo do ranking em 100%
 * (ou o fundo em 0%) por ruído estatístico — ex.: um dealer com 1 único VIN
 * elegível, atendido naquele mês, aparece "melhor" que unidades de centenas
 * de veículos que só não bateram 100% cheio. 20 filtra esse ruído sem
 * descartar concessionárias genuinamente pequenas.
 */
const MIN_VEICULOS = 20;

interface BarraConcessionaria {
  dealerCode: string;
  rotulo: string;
  valor: number;
}

/*
 * Mesma cor sólida única do ranking por modelo — ver justificativa em
 * VinShareModeloChart (categoria nominal com uma única métrica, o comprimento
 * da barra é quem carrega a magnitude).
 */
const COR_BARRA = "#00095b"; // --azul-800
const COR_CURSOR = "#eef1f8"; // --neutro-100
const COR_ROTULO = "#151a29"; // --cor-texto (--neutro-900)

const ALTURA_MINIMA = 160;
const ALTURA_POR_BARRA = 28;

/**
 * Ranking das top {@link TOP_N} concessionárias por VIN Share na competência mais
 * recente disponível.
 *
 * Par direto de `VinShareModeloChart`, mesma lógica (mesmo `GET /api/trend`, só que
 * `/concessionarias`; mesmo descarte de mês truncado; mesmo filtro de `valor === 0`
 * — ver os dois motivos lá). Duas diferenças: o corte pro top {@link TOP_N} (o
 * histórico tem ~434 concessionárias contra ~20 modelos — um ranking com todas seria
 * ilegível, ninguém rola 434 barras) e o piso `minVeiculos` pedido à API (dealers de
 * 1-2 VINs elegíveis, sem esse piso, entopem o topo em 100% por ruído estatístico,
 * não por volume real). A legenda deixa claro que é um recorte, não a rede inteira.
 */
export default function VinShareConcessionariaChart() {
  const { data, loading, error, recarregar } = useTrendConcessionariasData({ minVeiculos: MIN_VEICULOS });

  const competencia = useMemo(() => (data ? competenciaDeReferencia(data) : undefined), [data]);

  const totalNaCompetencia = useMemo(
    () => (data && competencia ? data.filter((ponto) => ponto.data === competencia && ponto.valor > 0).length : 0),
    [data, competencia]
  );

  const barras = useMemo<BarraConcessionaria[]>(() => {
    if (!data || !competencia) return [];
    return data
      .filter((ponto) => ponto.data === competencia && ponto.valor > 0)
      .map((ponto) => ({
        dealerCode: ponto.categoria,
        rotulo: rotuloDaConcessionaria(ponto.categoria),
        valor: ponto.valor
      }))
      .sort((a, b) => b.valor - a.valor)
      .slice(0, TOP_N);
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
          <p className="placeholder-texto">Carregando ranking por concessionária…</p>
        </div>
      ) : barras.length === 0 || !competencia ? (
        <div className="grafico-estado">
          <p className="placeholder-texto">Nenhum dado de VIN Share por concessionária para este recorte.</p>
        </div>
      ) : (
        <>
          <p className="grafico-legenda">
            Competência de referência: <strong>{formatarCompetenciaLonga(competencia)}</strong> · top{" "}
            {barras.length} de {totalNaCompetencia} concessionárias com pelo menos {MIN_VEICULOS} veículos
            elegíveis
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
                <YAxis type="category" dataKey="rotulo" width={130} />
                <Tooltip
                  cursor={{ fill: COR_CURSOR }}
                  formatter={(valor: number) => [`${valor}%`, "VIN Share"]}
                  labelFormatter={(rotulo: string) => rotulo}
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
