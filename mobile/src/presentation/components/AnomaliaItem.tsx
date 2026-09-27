import { Pressable, StyleSheet, Text, View } from "react-native";
import type { Anomaly, VinShareFiltros } from "../../domain/types";
import { nivelDeRisco, type NivelRisco } from "../../domain/severidade";
import { atalhoDaAnomalia } from "../atalhos";
import { formatarPercentual } from "../formatadores";
import { corDoNivel, cores, espaco, peso, raio, texto } from "../theme";

export interface AnomaliaItemProps {
  anomalia: Anomaly;
  onFiltrar: (filtro: Partial<VinShareFiltros>) => void;
}

const ROTULO_NIVEL: Record<NivelRisco, string> = {
  alto: "Severidade alta",
  medio: "Severidade média",
  baixo: "Severidade baixa"
};

export default function AnomaliaItem({ anomalia, onFiltrar }: AnomaliaItemProps) {
  const nivel = nivelDeRisco(anomalia.severidade);
  const { cor, fundo } = corDoNivel(nivel);
  const percentual = Math.round(anomalia.severidade * 100);
  const atalho = atalhoDaAnomalia(anomalia);
  const emAlta = anomalia.valorAtual > anomalia.valorReferencia;

  return (
    <View style={[estilos.card, { borderLeftColor: cor, backgroundColor: nivel === "baixo" ? cores.superficie : fundo }]}>
      <View style={estilos.cabecalho}>
        <Text style={estilos.entidade}>{anomalia.entidade}</Text>
        <Text style={[estilos.selo, { color: cor }]}>
          {ROTULO_NIVEL[nivel]} · {percentual}%
        </Text>
      </View>

      <Text style={estilos.resumo}>
        {emAlta ? "▲ " : "▼ "}
        {anomalia.resumo}
      </Text>

      <View style={estilos.comparacao}>
        <Text style={estilos.comparacaoReferencia}>{formatarPercentual(anomalia.valorReferencia)}</Text>
        <Text style={estilos.comparacaoSeta}>→</Text>
        <Text style={[estilos.comparacaoAtual, { color: nivel === "baixo" ? cores.texto : cor }]}>
          {formatarPercentual(anomalia.valorAtual)}
        </Text>
      </View>

      <View style={estilos.barra}>
        <View style={[estilos.barraPreenchida, { width: `${percentual}%`, backgroundColor: cor }]} />
      </View>

      {atalho && (
        <Pressable onPress={() => onFiltrar(atalho.filtro)}>
          <Text style={estilos.link}>{atalho.rotulo}</Text>
        </Pressable>
      )}
    </View>
  );
}

const estilos = StyleSheet.create({
  card: {
    padding: espaco[4],
    borderWidth: 1,
    borderColor: cores.borda,
    borderLeftWidth: 4,
    borderRadius: raio.sm,
    gap: espaco[1]
  },
  cabecalho: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: espaco[2]
  },
  entidade: {
    fontSize: texto.md,
    fontWeight: peso.medio,
    color: cores.texto,
    flexShrink: 1
  },
  selo: {
    fontSize: texto["2xs"],
    fontWeight: peso.forte,
    letterSpacing: 0.5,
    textTransform: "uppercase"
  },
  resumo: {
    fontSize: texto.sm,
    fontWeight: peso.medio,
    color: cores.texto
  },
  comparacao: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: espaco[2],
    marginTop: espaco[1]
  },
  comparacaoReferencia: {
    fontSize: texto.lg,
    fontWeight: peso.forte,
    color: cores.textoSuave
  },
  comparacaoSeta: {
    color: cores.neutro400
  },
  comparacaoAtual: {
    fontSize: texto.lg,
    fontWeight: peso.forte
  },
  barra: {
    height: 6,
    borderRadius: raio.pilula,
    backgroundColor: cores.neutro200,
    overflow: "hidden"
  },
  barraPreenchida: {
    height: "100%",
    borderRadius: raio.pilula
  },
  link: {
    marginTop: espaco[1],
    fontSize: texto.sm,
    color: cores.marcaClara,
    textDecorationLine: "underline"
  }
});
