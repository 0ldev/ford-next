import { StyleSheet, Text, View } from "react-native";
import { cores, espaco, peso, texto } from "../../theme";

export interface BarraRanking {
  chave: string;
  rotulo: string;
  valor: number;
}

export interface RankingBarChartProps {
  barras: BarraRanking[];
  corBarra?: string;
}

export default function RankingBarChart({ barras, corBarra = cores.azul800 }: RankingBarChartProps) {
  const valorMaximo = Math.max(10, ...barras.map((barra) => barra.valor));

  return (
    <View style={estilos.container}>
      {barras.map((barra) => {
        const largura = Math.max(2, (barra.valor / valorMaximo) * 100);
        return (
          <View key={barra.chave} style={estilos.linha}>
            <Text style={estilos.rotulo} numberOfLines={1}>
              {barra.rotulo}
            </Text>
            <View style={estilos.trilho}>
              <View style={[estilos.barra, { width: `${largura}%`, backgroundColor: corBarra }]} />
            </View>
            <Text style={estilos.valor}>{barra.valor}%</Text>
          </View>
        );
      })}
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    gap: espaco[3]
  },
  linha: {
    flexDirection: "row",
    alignItems: "center",
    gap: espaco[2]
  },
  rotulo: {
    width: 108,
    fontSize: texto.xs,
    color: cores.texto
  },
  trilho: {
    flex: 1,
    height: 16,
    borderRadius: 4,
    backgroundColor: cores.neutro100,
    overflow: "hidden"
  },
  barra: {
    height: "100%",
    borderRadius: 4
  },
  valor: {
    width: 42,
    textAlign: "right",
    fontSize: texto.xs,
    fontWeight: peso.medio,
    color: cores.texto
  }
});
