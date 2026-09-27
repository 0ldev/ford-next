import { Pressable, StyleSheet, Text, View } from "react-native";
import { cores, espaco, peso, raio, texto } from "../theme";

export interface EstadoErroProps {
  mensagem: string;
  onTentarNovamente?: () => void;
}

export default function EstadoErro({ mensagem, onTentarNovamente }: EstadoErroProps) {
  return (
    <View style={estilos.container}>
      <Text style={estilos.mensagem}>{mensagem}</Text>
      {onTentarNovamente && (
        <Pressable style={estilos.botao} onPress={onTentarNovamente}>
          <Text style={estilos.botaoTexto}>Tentar novamente</Text>
        </Pressable>
      )}
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    gap: espaco[3]
  },
  mensagem: {
    fontSize: texto.md,
    color: cores.erro
  },
  botao: {
    alignSelf: "flex-start",
    height: 38,
    paddingHorizontal: espaco[4],
    borderWidth: 1,
    borderColor: cores.marca,
    borderRadius: raio.sm,
    alignItems: "center",
    justifyContent: "center"
  },
  botaoTexto: {
    fontSize: texto.sm,
    fontWeight: peso.medio,
    color: cores.marca
  }
});
