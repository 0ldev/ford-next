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
import { useScoreDistribution } from "../application/useScoreDistribution";
import EstadoErro from "./EstadoErro";

/*
 * Mesma cor sólida única dos rankings por modelo/concessionária — aqui a ordem das
 * faixas já é o eixo X, então a cor não precisa (nem deve) carregar informação extra.
 */
const COR_BARRA = "#00095b"; // --azul-800
const COR_CURSOR = "#eef1f8"; // --neutro-100
const COR_ROTULO = "#151a29"; // --cor-texto (--neutro-900)

const formatadorInteiro = new Intl.NumberFormat("pt-BR");

interface BarraFaixa {
  faixa: string;
  quantidade: number;
}

/**
 * Distribuição do score de risco de evasão em toda a base de leads (~175 mil VINs,
 * não o top 50 de `/api/leads`).
 *
 * A forma é o ponto do gráfico: o score é fortemente bimodal — a maior parte da
 * frota perto de 0% ou perto de 100%, quase nada no meio. Não é ruído de
 * visualização: é consequência direta de como o score é montado (heurística binária
 * 0/1 pros modelos de baixo volume; o modelo de ML, com AUC≈1.0 no baseline, também
 * satura perto dos extremos — ver `domain.action_rules` no backend). A escala do
 * eixo Y é linear de propósito: um eixo logarítmico esconderia exatamente o
 * desequilíbrio que este gráfico existe para mostrar.
 */
export default function ScoreDistributionChart() {
  const { data, loading, error, recarregar } = useScoreDistribution();

  const barras = useMemo<BarraFaixa[]>(() => {
    if (!data) return [];
    return [...data]
      .sort((a, b) => a.faixaInicio - b.faixaInicio)
      .map((faixa) => ({
        faixa: `${faixa.faixaInicio}-${faixa.faixaFim}%`,
        quantidade: faixa.quantidade
      }));
  }, [data]);

  const total = useMemo(() => barras.reduce((soma, barra) => soma + barra.quantidade, 0), [barras]);

  return (
    <div className="grafico">
      {error ? (
        <div className="grafico-estado">
          <EstadoErro mensagem={error.message} onTentarNovamente={recarregar} />
        </div>
      ) : loading ? (
        <div className="grafico-estado" role="status">
          <p className="placeholder-texto">Carregando distribuição de score…</p>
        </div>
      ) : barras.length === 0 ? (
        <div className="grafico-estado">
          <p className="placeholder-texto">Nenhum dado de distribuição de score disponível.</p>
        </div>
      ) : (
        <>
          <p className="grafico-legenda">
            <strong>{formatadorInteiro.format(total)}</strong> veículos avaliados
          </p>
          <div className="grafico-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barras} margin={{ top: 24, right: 16, bottom: 4, left: 8 }} barCategoryGap={8}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="faixa" />
                <YAxis width={64} tickFormatter={(valor: number) => formatadorInteiro.format(valor)} />
                <Tooltip
                  cursor={{ fill: COR_CURSOR }}
                  formatter={(valor: number) => [formatadorInteiro.format(valor), "Veículos"]}
                  labelFormatter={(faixa: string) => `Score ${faixa}`}
                />
                <Bar dataKey="quantidade" fill={COR_BARRA} radius={[4, 4, 0, 0]} maxBarSize={48}>
                  <LabelList
                    dataKey="quantidade"
                    position="top"
                    formatter={(valor: number) => formatadorInteiro.format(valor)}
                    fill={COR_ROTULO}
                    fontSize={11}
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
