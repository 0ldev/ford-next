import { Pressable, StyleSheet, Text, View } from "react-native";
import { cores, espaco, peso, raio, texto } from "../theme";

export interface SeletorModelosProps {
  opcoes: readonly string[];
  selecionados: string[];
  onChange: (selecionados: string[]) => void;
}

export default function SeletorModelos({ opcoes, selecionados, onChange }: SeletorModelosProps) {
  const nenhumMarcado = selecionados.length === 0;

  const alternar = (modelo: string) => {
    onChange(
      selecionados.includes(modelo)
        ? selecionados.filter((item) => item !== modelo)
        : [...selecionados, modelo]
    );
  };

  return (
    <View style={estilos.container}>
      <Text style={estilos.rotulo}>Modelos no gráfico</Text>
      <View style={estilos.opcoes}>
        {opcoes.map((modelo) => {
          const ativo = selecionados.includes(modelo);
          return (
            <Pressable
              key={modelo}
              style={({ pressed }) => [estilos.chip, ativo && estilos.chipAtivo, pressed && estilos.chipPressionado]}
              onPress={() => alternar(modelo)}
            >
              <Text style={[estilos.chipTexto, ativo && estilos.chipTextoAtivo]}>{modelo}</Text>
            </Pressable>
          );
        })}
        {!nenhumMarcado && (
          <Pressable onPress={() => onChange([])}>
            <Text style={estilos.limpar}>Mostrar todos</Text>
          </Pressable>
        )}
      </View>
      {nenhumMarcado && <Text style={estilos.dica}>Nenhum modelo marcado: exibindo todos.</Text>}
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    gap: espaco[2]
  },
  rotulo: {
    fontSize: texto.xs,
    fontWeight: peso.medio,
    color: cores.textoSuave
  },
  opcoes: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: espaco[2],
    alignItems: "center"
  },
  chip: {
    paddingHorizontal: espaco[3],
    paddingVertical: espaco[1],
    borderRadius: raio.pilula,
    borderWidth: 1,
    borderColor: cores.borda,
    backgroundColor: cores.superficie
  },
  chipAtivo: {
    backgroundColor: cores.azul100,
    borderColor: cores.marcaClara
  },
  chipPressionado: {
    opacity: 0.7
  },
  chipTexto: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  chipTextoAtivo: {
    color: cores.marca,
    fontWeight: peso.medio
  },
  limpar: {
    fontSize: texto.sm,
    color: cores.marcaClara,
    textDecorationLine: "underline"
  },
  dica: {
    fontSize: texto.xs,
    color: cores.textoSuave
  }
});
