import { useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useFiltros } from "../../application/FiltrosContext";
import { useScoreDistribution } from "../../application/useScoreDistribution";
import { useTrendConcessionariasData } from "../../application/useTrendConcessionariasData";
import { useTrendData } from "../../application/useTrendData";
import { competenciaDeReferencia, formatarCompetenciaLonga } from "../../domain/competencia";
import { rotuloDaConcessionaria } from "../../infrastructure/mockData";
import Cabecalho from "../components/Cabecalho";
import EstadoErro from "../components/EstadoErro";
import Secao from "../components/Secao";
import SeletorModelos from "../components/SeletorModelos";
import HistogramaChart from "../components/charts/HistogramaChart";
import LinhaTendenciaChart from "../components/charts/LinhaTendenciaChart";
import RankingBarChart from "../components/charts/RankingBarChart";
import { formatarInteiro } from "../formatadores";
import { pivotarPorMes } from "../pivot";
import { CORES_SERIE, cores, espaco, texto } from "../theme";

const TOP_N_CONCESSIONARIAS = 15;
const MIN_VEICULOS_CONCESSIONARIA = 20;

function paraCompetencia(dataIso?: string): string | undefined {
  return dataIso?.slice(0, 7);
}

export default function TendenciaScreen() {
  const { filtros, catalogo } = useFiltros();
  const [modelosSelecionados, setModelosSelecionados] = useState<string[]>([]);

  const periodoInicio = paraCompetencia(filtros.periodoInicio);
  const periodoFim = paraCompetencia(filtros.periodoFim);
  const modelosCatalogo = catalogo?.modelos ?? [];

  const { data: trend, loading: carregandoTrend, error: erroTrend, recarregar: recarregarTrend } = useTrendData({
    modelo: modelosSelecionados,
    periodoInicio,
    periodoFim
  });

  const linhas = useMemo(() => (trend ? pivotarPorMes(trend) : []), [trend]);
  const series = useMemo(() => (trend ? [...new Set(trend.map((ponto) => ponto.categoria))] : []), [trend]);

  const {
    data: trendModelo,
    loading: carregandoModelo,
    error: erroModelo,
    recarregar: recarregarModelo
  } = useTrendData({ periodoInicio, periodoFim });

  const competenciaModelo = useMemo(
    () => (trendModelo ? competenciaDeReferencia(trendModelo) : undefined),
    [trendModelo]
  );

  const barrasModelo = useMemo(() => {
    if (!trendModelo || !competenciaModelo) return [];
    return trendModelo
      .filter((ponto) => ponto.data === competenciaModelo && ponto.valor > 0)
      .map((ponto) => ({ chave: ponto.categoria, rotulo: ponto.categoria, valor: ponto.valor }))
      .sort((a, b) => b.valor - a.valor);
  }, [trendModelo, competenciaModelo]);

  const {
    data: trendConcessionaria,
    loading: carregandoConcessionaria,
    error: erroConcessionaria,
    recarregar: recarregarConcessionaria
  } = useTrendConcessionariasData({ minVeiculos: MIN_VEICULOS_CONCESSIONARIA });

  const competenciaConcessionaria = useMemo(
    () => (trendConcessionaria ? competenciaDeReferencia(trendConcessionaria) : undefined),
    [trendConcessionaria]
  );

  const barrasConcessionaria = useMemo(() => {
    if (!trendConcessionaria || !competenciaConcessionaria) return [];
    return trendConcessionaria
      .filter((ponto) => ponto.data === competenciaConcessionaria && ponto.valor > 0)
      .map((ponto) => ({
        chave: ponto.categoria,
        rotulo: rotuloDaConcessionaria(ponto.categoria),
        valor: ponto.valor
      }))
      .sort((a, b) => b.valor - a.valor)
      .slice(0, TOP_N_CONCESSIONARIAS);
  }, [trendConcessionaria, competenciaConcessionaria]);

  const {
    data: distribuicao,
    loading: carregandoDistribuicao,
    error: erroDistribuicao,
    recarregar: recarregarDistribuicao
  } = useScoreDistribution();

  const barrasHistograma = useMemo(() => {
    if (!distribuicao) return [];
    return [...distribuicao]
      .sort((a, b) => a.faixaInicio - b.faixaInicio)
      .map((faixa) => ({ faixa: `${faixa.faixaInicio}-${faixa.faixaFim}%`, quantidade: faixa.quantidade }));
  }, [distribuicao]);

  const totalAvaliados = useMemo(
    () => barrasHistograma.reduce((soma, barra) => soma + barra.quantidade, 0),
    [barrasHistograma]
  );

  return (
    <View style={estilos.tela}>
      <Cabecalho titulo="Tendência" subtitulo="Evolução do VIN Share no tempo e rankings do período." mostrarFiltros />

      <ScrollView contentContainerStyle={estilos.conteudo}>
        <Secao titulo="Tendência de VIN Share">
          <SeletorModelos opcoes={modelosCatalogo} selecionados={modelosSelecionados} onChange={setModelosSelecionados} />

          {erroTrend ? (
            <EstadoErro mensagem={erroTrend.message} onTentarNovamente={recarregarTrend} />
          ) : carregandoTrend ? (
            <Text style={estilos.placeholder}>Carregando série temporal…</Text>
          ) : linhas.length === 0 ? (
            <Text style={estilos.placeholder}>Nenhum dado de tendência para este recorte.</Text>
          ) : (
            <>
              <LinhaTendenciaChart linhas={linhas} series={series} cores={CORES_SERIE} />
              <View style={estilos.legenda}>
                {series.map((serie, indice) => (
                  <View key={serie} style={estilos.legendaItem}>
                    <View style={[estilos.legendaCor, { backgroundColor: CORES_SERIE[indice % CORES_SERIE.length] }]} />
                    <Text style={estilos.legendaTexto}>{serie}</Text>
                  </View>
                ))}
              </View>
            </>
          )}
        </Secao>

        <Secao titulo="VIN Share por modelo">
          {erroModelo ? (
            <EstadoErro mensagem={erroModelo.message} onTentarNovamente={recarregarModelo} />
          ) : carregandoModelo ? (
            <Text style={estilos.placeholder}>Carregando ranking por modelo…</Text>
          ) : barrasModelo.length === 0 || !competenciaModelo ? (
            <Text style={estilos.placeholder}>Nenhum dado de VIN Share por modelo para este recorte.</Text>
          ) : (
            <>
              <Text style={estilos.legendaGrafico}>
                Competência de referência: <Text style={estilos.negrito}>{formatarCompetenciaLonga(competenciaModelo)}</Text>
              </Text>
              <RankingBarChart barras={barrasModelo} />
            </>
          )}
        </Secao>

        <Secao titulo="VIN Share por concessionária">
          {erroConcessionaria ? (
            <EstadoErro mensagem={erroConcessionaria.message} onTentarNovamente={recarregarConcessionaria} />
          ) : carregandoConcessionaria ? (
            <Text style={estilos.placeholder}>Carregando ranking por concessionária…</Text>
          ) : barrasConcessionaria.length === 0 || !competenciaConcessionaria ? (
            <Text style={estilos.placeholder}>Nenhum dado de VIN Share por concessionária para este recorte.</Text>
          ) : (
            <>
              <Text style={estilos.legendaGrafico}>
                Competência de referência:{" "}
                <Text style={estilos.negrito}>{formatarCompetenciaLonga(competenciaConcessionaria)}</Text> · top{" "}
                {barrasConcessionaria.length} concessionárias com pelo menos {MIN_VEICULOS_CONCESSIONARIA} veículos
                elegíveis
              </Text>
              <RankingBarChart barras={barrasConcessionaria} />
            </>
          )}
        </Secao>

        <Secao titulo="Distribuição de score de risco">
          {erroDistribuicao ? (
            <EstadoErro mensagem={erroDistribuicao.message} onTentarNovamente={recarregarDistribuicao} />
          ) : carregandoDistribuicao ? (
            <Text style={estilos.placeholder}>Carregando distribuição de score…</Text>
          ) : barrasHistograma.length === 0 ? (
            <Text style={estilos.placeholder}>Nenhum dado de distribuição de score disponível.</Text>
          ) : (
            <>
              <Text style={estilos.legendaGrafico}>
                <Text style={estilos.negrito}>{formatarInteiro(totalAvaliados)}</Text> veículos avaliados
              </Text>
              <HistogramaChart barras={barrasHistograma} altura={200} />
            </>
          )}
        </Secao>
      </ScrollView>
    </View>
  );
}

const estilos = StyleSheet.create({
  tela: {
    flex: 1,
    backgroundColor: cores.fundo
  },
  conteudo: {
    padding: espaco[4],
    gap: espaco[4]
  },
  placeholder: {
    fontSize: texto.md,
    color: cores.textoSuave,
    paddingVertical: espaco[5],
    textAlign: "center"
  },
  legenda: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: espaco[3],
    marginTop: espaco[2]
  },
  legendaItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: espaco[1]
  },
  legendaCor: {
    width: 10,
    height: 10,
    borderRadius: 5
  },
  legendaTexto: {
    fontSize: texto.xs,
    color: cores.texto
  },
  legendaGrafico: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  negrito: {
    color: cores.texto,
    fontWeight: "700"
  }
});
