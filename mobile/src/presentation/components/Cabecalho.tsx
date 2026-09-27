import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { cores, espaco, peso, raio, texto } from "../theme";

export interface CabecalhoProps {
  titulo: string;
  subtitulo?: string;
  mostrarFiltros?: boolean;
}

export default function Cabecalho({ titulo, subtitulo, mostrarFiltros = false }: CabecalhoProps) {
  const router = useRouter();

  return (
    <View style={estilos.container}>
      <View style={estilos.linha}>
        <View style={estilos.marca}>
          <Text style={estilos.marcaTexto}>VS</Text>
        </View>
        <View style={estilos.textos}>
          <Text style={estilos.titulo}>{titulo}</Text>
          {subtitulo && <Text style={estilos.subtitulo}>{subtitulo}</Text>}
        </View>
      </View>

      {mostrarFiltros && (
        <Pressable
          style={({ pressed }) => [estilos.botaoFiltros, pressed && estilos.botaoFiltrosPressionado]}
          onPress={() => router.push("/filtros")}
        >
          <Text style={estilos.botaoFiltrosTexto}>Filtros</Text>
        </Pressable>
      )}
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    borderBottomWidth: 3,
    borderBottomColor: cores.marca,
    paddingHorizontal: espaco[4],
    paddingTop: espaco[5],
    paddingBottom: espaco[4],
    backgroundColor: cores.superficie,
    gap: espaco[3]
  },
  linha: {
    flexDirection: "row",
    alignItems: "center",
    gap: espaco[3]
  },
  marca: {
    width: 56,
    height: 32,
    borderRadius: raio.pilula,
    backgroundColor: cores.azul800,
    alignItems: "center",
    justifyContent: "center"
  },
  marcaTexto: {
    color: cores.branco,
    fontFamily: "serif",
    fontStyle: "italic",
    fontWeight: peso.forte,
    fontSize: texto.md
  },
  textos: {
    flex: 1
  },
  titulo: {
    fontSize: texto.xl,
    fontWeight: peso.forte,
    color: cores.azul900
  },
  subtitulo: {
    marginTop: 2,
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  botaoFiltros: {
    alignSelf: "flex-start",
    height: 36,
    paddingHorizontal: espaco[4],
    borderRadius: raio.sm,
    borderWidth: 1,
    borderColor: cores.marca,
    alignItems: "center",
    justifyContent: "center"
  },
  botaoFiltrosPressionado: {
    backgroundColor: cores.azul100
  },
  botaoFiltrosTexto: {
    fontSize: texto.sm,
    fontWeight: peso.medio,
    color: cores.marca
  }
});
