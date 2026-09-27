import { StyleSheet, Text, View } from "react-native";
import { formatarInteiro } from "../../formatadores";
import { cores, espaco, peso } from "../../theme";

export interface BarraHistograma {
  faixa: string;
  quantidade: number;
}

export interface HistogramaChartProps {
  barras: BarraHistograma[];
  altura?: number;
}

export default function HistogramaChart({ barras, altura = 160 }: HistogramaChartProps) {
  const valorMaximo = Math.max(1, ...barras.map((barra) => barra.quantidade));

  return (
    <View style={[estilos.container, { height: altura }]}>
      {barras.map((barra) => {
        const alturaBarra = Math.max(2, (barra.quantidade / valorMaximo) * (altura - 44));
        return (
          <View key={barra.faixa} style={estilos.coluna}>
            <Text style={estilos.valor} numberOfLines={1}>
              {formatarInteiro(barra.quantidade)}
            </Text>
            <View style={[estilos.barra, { height: alturaBarra }]} />
            <Text style={estilos.faixa}>{barra.faixa}</Text>
          </View>
        );
      })}
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: espaco[1]
  },
  coluna: {
    flex: 1,
    alignItems: "center",
    justifyContent: "flex-end",
    gap: espaco[1]
  },
  barra: {
    width: "100%",
    borderRadius: 4,
    backgroundColor: cores.azul800
  },
  valor: {
    fontSize: 9,
    color: cores.texto,
    fontWeight: peso.medio
  },
  faixa: {
    fontSize: 9,
    color: cores.textoSuave,
    transform: [{ rotate: "-40deg" }]
  }
});
