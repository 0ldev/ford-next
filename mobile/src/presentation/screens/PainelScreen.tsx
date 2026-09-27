import { ScrollView, StyleSheet, View } from "react-native";
import { useFiltros } from "../../application/FiltrosContext";
import { useAnomaliesData } from "../../application/useAnomaliesData";
import { useVinShareData } from "../../application/useVinShareData";
import { formatarInteiro } from "../formatadores";
import { cores, espaco } from "../theme";
import AcaoPrioritariaKpiCard from "../components/AcaoPrioritariaKpiCard";
import Cabecalho from "../components/Cabecalho";
import KpiCard, { type ComparacaoKpi } from "../components/KpiCard";
import ResumoFiltros from "../components/ResumoFiltros";
import Secao from "../components/Secao";

export default function PainelScreen() {
  const { filtros } = useFiltros();
  const { data, loading, error, recarregar } = useVinShareData(filtros);
  const { data: referencia } = useVinShareData({
    periodoInicio: filtros.periodoInicio,
    periodoFim: filtros.periodoFim
  });
  const {
    data: anomalias,
    loading: carregandoAnomalias,
    error: erroAnomalias,
    recarregar: recarregarAnomalias
  } = useAnomaliesData();

  const temFiltroDemografico = Boolean(
    filtros.concessionaria || filtros.modelo || filtros.faixaIdade || filtros.tipoServico
  );

  const comparacao: ComparacaoKpi | undefined =
    temFiltroDemografico && referencia ? { base: referencia.vinShareEstimado, rotuloBase: "média da rede" } : undefined;

  const contexto = data
    ? `${formatarInteiro(data.totalComServico)} de ${formatarInteiro(data.totalVeiculosElegiveis)} veículos elegíveis passaram pela rede oficial`
    : undefined;

  return (
    <View style={estilos.tela}>
      <Cabecalho
        titulo="VIN Share Intelligence Hub"
        subtitulo="Retenção de pós-venda da rede Ford: onde o VIN Share está caindo, por que, e quem contatar primeiro."
        mostrarFiltros
      />

      <ScrollView contentContainerStyle={estilos.conteudo}>
        <Secao titulo="Recorte ativo">
          <ResumoFiltros filtros={filtros} />
        </Secao>

        <Secao titulo="Indicadores">
          <View style={estilos.indicadores}>
            <KpiCard
              label="VIN Share estimado"
              valor={data?.vinShareEstimado}
              contexto={contexto}
              comparacao={comparacao}
              loading={loading}
              erro={error ? error.message : null}
              onTentarNovamente={recarregar}
            />

            <KpiCard
              label="Anomalias detectadas"
              valor={anomalias?.length}
              unidade=""
              casasDecimais={0}
              loading={carregandoAnomalias}
              erro={erroAnomalias ? erroAnomalias.message : null}
              onTentarNovamente={recarregarAnomalias}
            />

            <AcaoPrioritariaKpiCard concessionaria={filtros.concessionaria} />
          </View>
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
  indicadores: {
    gap: espaco[3]
  }
});
