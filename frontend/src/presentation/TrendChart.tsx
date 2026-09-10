import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { useTrendData } from "../application/useTrendData";
import type { TrendResponse } from "../domain/types";
import EstadoErro from "./EstadoErro";
import SeletorModelos from "./SeletorModelos";

export interface TrendChartProps {
  /** Recorte de período herdado dos filtros da página. */
  periodoInicio?: string;
  periodoFim?: string;
  /** Catálogo real de modelos (via `useCatalogo`), não uma lista fixa no frontend. */
  modelos: string[];
}

/*
 * Paleta das séries. O SVG do Recharts recebe cor por prop, então estes
 * valores não podem vir de custom properties; a primeira é o azul da marca
 * (--azul-800) e as demais foram escolhidas para se distinguirem dela e
 * entre si. Grade, eixos e legenda, esses sim, são estilizados por CSS.
 */
const CORES_SERIE = ["#00095b", "#c2410c", "#0b7a5a", "#6d28d9", "#0284c7", "#a16207"];

/**
 * Cor fixa por modelo, ancorada na posição dele no catálogo (`modelos`).
 *
 * Se a cor viesse da ordem das séries desenhadas, desmarcar um modelo
 * recoloriria os outros e a comparação entre duas seleções ficaria enganosa.
 */
function corDoModelo(modelo: string, posicaoNaSerie: number, modelos: string[]): string {
  const indice = modelos.indexOf(modelo);
  return CORES_SERIE[(indice >= 0 ? indice : posicaoNaSerie) % CORES_SERIE.length];
}

/** Linha do gráfico: a competência mais o valor de cada modelo naquele mês. */
interface PontoGrafico {
  data: string;
  [modelo: string]: string | number;
}

/**
 * A API devolve os pontos em formato longo (uma linha por modelo/mês) e o
 * Recharts desenha a partir do formato largo (uma linha por mês, uma coluna
 * por modelo). Esta é a virada entre os dois.
 */
export function pivotarPorMes(pontos: TrendResponse): PontoGrafico[] {
  const porMes = new Map<string, PontoGrafico>();

  for (const ponto of pontos) {
    const linha = porMes.get(ponto.data) ?? { data: ponto.data };
    linha[ponto.categoria] = ponto.valor;
    porMes.set(ponto.data, linha);
  }

  return [...porMes.values()].sort((a, b) => a.data.localeCompare(b.data));
}

const MESES_CURTOS = [
  "jan",
  "fev",
  "mar",
  "abr",
  "mai",
  "jun",
  "jul",
  "ago",
  "set",
  "out",
  "nov",
  "dez"
];

/** "2026-01" vira "jan/26", que cabe no eixo sem sobrepor. */
export function formatarCompetencia(competencia: string): string {
  const [ano, mes] = competencia.split("-");
  const indice = Number(mes) - 1;
  if (!ano || Number.isNaN(indice) || !MESES_CURTOS[indice]) return competencia;
  return `${MESES_CURTOS[indice]}/${ano.slice(2)}`;
}

/**
 * Tendência de VIN Share ao longo do tempo, uma linha por modelo.
 *
 * A seleção de modelos é local ao gráfico: o filtro de modelo da barra
 * superior é de seleção única e serve aos indicadores, enquanto aqui o
 * objetivo é justamente comparar modelos entre si.
 */
export default function TrendChart({ periodoInicio, periodoFim, modelos }: TrendChartProps) {
  const [modelosSelecionados, setModelosSelecionados] = useState<string[]>([]);

  const { data, loading, error, recarregar } = useTrendData({
    modelo: modelosSelecionados,
    periodoInicio,
    periodoFim
  });

  const linhas = useMemo(() => (data ? pivotarPorMes(data) : []), [data]);

  // As séries vêm do próprio dado, não da seleção: assim o gráfico continua
  // correto se a API devolver um modelo a mais ou a menos que o pedido.
  const series = useMemo(
    () => (data ? [...new Set(data.map((ponto) => ponto.categoria))] : []),
    [data]
  );

  return (
    <div className="grafico">
      <SeletorModelos
        opcoes={modelos}
        selecionados={modelosSelecionados}
        onChange={setModelosSelecionados}
      />

      {error ? (
        <div className="grafico-estado">
          <EstadoErro mensagem={error.message} onTentarNovamente={recarregar} />
        </div>
      ) : loading ? (
        <div className="grafico-estado" role="status">
          <p className="placeholder-texto">Carregando série temporal…</p>
        </div>
      ) : linhas.length === 0 ? (
        <div className="grafico-estado">
          <p className="placeholder-texto">Nenhum dado de tendência para este recorte.</p>
        </div>
      ) : (
        <div className="grafico-area">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={linhas} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="data" tickFormatter={formatarCompetencia} />
              <YAxis
                width={56}
                tickFormatter={(valor: number) => `${valor}%`}
                domain={[0, "auto"]}
              />
              <Tooltip
                formatter={(valor: number) => `${valor}%`}
                labelFormatter={formatarCompetencia}
              />
              <Legend />
              {series.map((modelo, indice) => (
                <Line
                  key={modelo}
                  type="monotone"
                  dataKey={modelo}
                  name={modelo}
                  stroke={corDoModelo(modelo, indice, modelos)}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
