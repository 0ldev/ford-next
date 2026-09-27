import { useRouter } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useFiltros } from "../../application/FiltrosContext";
import { useAnomaliesData } from "../../application/useAnomaliesData";
import type { Anomaly, AnomalyTipo, VinShareFiltros } from "../../domain/types";
import { atalhoDaAnomalia } from "../atalhos";
import AnomaliaItem from "../components/AnomaliaItem";
import Cabecalho from "../components/Cabecalho";
import EstadoErro from "../components/EstadoErro";
import Secao from "../components/Secao";
import { cores, espaco, peso, raio, texto } from "../theme";

const GRUPOS: { tipo: AnomalyTipo; titulo: string; descricao: string }[] = [
  {
    tipo: "queda_dealer",
    titulo: "Quedas abruptas por concessionária",
    descricao: "Unidades perdendo retenção rápido demais para ser sazonalidade."
  },
  {
    tipo: "gap_modelo",
    titulo: "Gap crescente por modelo",
    descricao: "Modelos que se afastam da média de VIN Share da rede."
  },
  {
    tipo: "pico_mainsource",
    titulo: "Picos incomuns de origem",
    descricao: "Serviços migrando para fora da rede oficial."
  }
];

export default function AnomaliasScreen() {
  const router = useRouter();
  const { atualizarFiltros } = useFiltros();
  const { data, loading, error, recarregar } = useAnomaliesData();

  const onFiltrar = (filtro: Partial<VinShareFiltros>) => {
    atualizarFiltros(filtro);
    router.navigate("/");
  };

  const anomalias: Anomaly[] = data ?? [];
  const maisSevera = anomalias.reduce<Anomaly | undefined>(
    (pior, atual) => (!pior || atual.severidade > pior.severidade ? atual : pior),
    undefined
  );
  const atalhoDoDestaque = maisSevera ? atalhoDaAnomalia(maisSevera) : null;

  return (
    <View style={estilos.tela}>
      <Cabecalho titulo="Anomalias" subtitulo="Alertas automáticos sobre o comportamento da rede." />

      <ScrollView contentContainerStyle={estilos.conteudo}>
        {error ? (
          <Secao titulo="Anomalias">
            <EstadoErro mensagem={error.message} onTentarNovamente={recarregar} />
          </Secao>
        ) : loading ? (
          <Secao titulo="Anomalias">
            <Text style={estilos.placeholder}>Carregando anomalias…</Text>
          </Secao>
        ) : (
          <>
            {maisSevera && (
              <View style={estilos.destaque}>
                <Text style={estilos.destaqueRotulo}>
                  Maior alerta · {Math.round(maisSevera.severidade * 100)}% de severidade
                </Text>
                <Text style={estilos.destaqueEntidade}>{maisSevera.entidade}</Text>
                <Text style={estilos.destaqueDescricao}>{maisSevera.descricao}</Text>
                {atalhoDoDestaque && (
                  <Text style={estilos.destaqueAcao} onPress={() => onFiltrar(atalhoDoDestaque.filtro)}>
                    {atalhoDoDestaque.rotulo}
                  </Text>
                )}
              </View>
            )}

            {GRUPOS.map((grupo) => {
              const doGrupo = anomalias
                .filter((anomalia) => anomalia.tipo === grupo.tipo)
                .sort((a, b) => b.severidade - a.severidade);

              return (
                <Secao key={grupo.tipo} titulo={`${grupo.titulo} (${doGrupo.length})`}>
                  <Text style={estilos.grupoDescricao}>{grupo.descricao}</Text>
                  {doGrupo.length === 0 ? (
                    <Text style={estilos.placeholder}>Nenhuma anomalia neste grupo.</Text>
                  ) : (
                    <View style={estilos.lista}>
                      {doGrupo.map((anomalia) => (
                        <AnomaliaItem
                          key={`${anomalia.tipo}-${anomalia.entidade}`}
                          anomalia={anomalia}
                          onFiltrar={onFiltrar}
                        />
                      ))}
                    </View>
                  )}
                </Secao>
              );
            })}
          </>
        )}
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
    paddingVertical: espaco[3]
  },
  destaque: {
    gap: espaco[1],
    padding: espaco[4],
    borderLeftWidth: 4,
    borderLeftColor: cores.riscoAlto,
    borderRadius: raio.sm,
    backgroundColor: cores.riscoAltoFundo
  },
  destaqueRotulo: {
    fontSize: texto["2xs"],
    fontWeight: peso.forte,
    letterSpacing: 0.5,
    textTransform: "uppercase",
    color: cores.riscoAlto
  },
  destaqueEntidade: {
    fontSize: texto.lg,
    fontWeight: peso.medio,
    color: cores.azul900
  },
  destaqueDescricao: {
    fontSize: texto.md,
    color: cores.texto
  },
  destaqueAcao: {
    marginTop: espaco[2],
    fontSize: texto.sm,
    fontWeight: peso.medio,
    color: cores.riscoAlto,
    textDecorationLine: "underline"
  },
  grupoDescricao: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  lista: {
    gap: espaco[3]
  }
});
