import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";
import { cores, espaco, peso, raio, texto } from "../theme";

export interface SecaoProps {
  titulo: string;
  children: ReactNode;
}

export default function Secao({ titulo, children }: SecaoProps) {
  return (
    <View style={estilos.secao}>
      <Text style={estilos.titulo}>{titulo}</Text>
      {children}
    </View>
  );
}

const estilos = StyleSheet.create({
  secao: {
    backgroundColor: cores.superficie,
    borderWidth: 1,
    borderColor: cores.borda,
    borderRadius: raio.md,
    padding: espaco[4],
    gap: espaco[4],
    shadowColor: cores.azul800,
    shadowOpacity: 0.06,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1
  },
  titulo: {
    fontSize: texto.xs,
    fontWeight: peso.forte,
    letterSpacing: 0.5,
    textTransform: "uppercase",
    color: cores.textoSuave
  }
});
