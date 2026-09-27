import * as Clipboard from "expo-clipboard";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { cores, espaco, peso, raio, texto } from "../theme";

export interface BotaoCopiarProps {
  texto: string;
  rotulo?: string;
}

type Estado = "parado" | "copiado" | "falhou";

export default function BotaoCopiar({ texto: textoParaCopiar, rotulo = "Copiar mensagem" }: BotaoCopiarProps) {
  const [estado, setEstado] = useState<Estado>("parado");

  useEffect(() => {
    if (estado === "parado") return;
    const id = setTimeout(() => setEstado("parado"), 2400);
    return () => clearTimeout(id);
  }, [estado]);

  const aoPressionar = async () => {
    try {
      await Clipboard.setStringAsync(textoParaCopiar);
      setEstado("copiado");
    } catch {
      setEstado("falhou");
    }
  };

  const corEstado =
    estado === "copiado" ? cores.verdePositivo : estado === "falhou" ? cores.riscoMedio : cores.marca;

  return (
    <Pressable
      onPress={aoPressionar}
      style={[estilos.botao, { borderColor: estado === "parado" ? cores.borda : corEstado }]}
    >
      <Text style={[estilos.icone, { color: corEstado }]}>{estado === "copiado" ? "✓" : "⧉"}</Text>
      <Text style={[estilos.texto, { color: corEstado }]}>
        {estado === "copiado" ? "Copiado" : estado === "falhou" ? "Não foi possível copiar" : rotulo}
      </Text>
    </Pressable>
  );
}

const estilos = StyleSheet.create({
  botao: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: espaco[2],
    height: 38,
    paddingHorizontal: espaco[4],
    borderWidth: 1,
    borderRadius: raio.sm,
    backgroundColor: cores.superficie
  },
  icone: {
    fontSize: texto.md
  },
  texto: {
    fontSize: texto.sm,
    fontWeight: peso.medio
  }
});
