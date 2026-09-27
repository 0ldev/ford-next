import { useState } from "react";
import { FlatList, Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { cores, espaco, peso, raio, texto } from "../theme";

export interface OpcaoSelecao {
  value: string;
  label: string;
}

export interface SelecaoProps {
  label: string;
  options: OpcaoSelecao[];
  value?: string;
  onChange: (value: string | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
}

export default function Selecao({
  label,
  options,
  value,
  onChange,
  placeholder = "Todos",
  disabled = false
}: SelecaoProps) {
  const [aberto, setAberto] = useState(false);
  const selecionada = options.find((opcao) => opcao.value === value);

  return (
    <View style={estilos.campo}>
      <Text style={estilos.label}>{label}</Text>
      <Pressable
        style={({ pressed }) => [
          estilos.controle,
          disabled && estilos.controleDesabilitado,
          pressed && !disabled && estilos.controlePressionado
        ]}
        onPress={() => !disabled && setAberto(true)}
      >
        <Text style={[estilos.valorTexto, !selecionada && estilos.placeholder]} numberOfLines={1}>
          {selecionada ? selecionada.label : placeholder}
        </Text>
        <Text style={estilos.seta}>▾</Text>
      </Pressable>

      <Modal visible={aberto} transparent animationType="slide" onRequestClose={() => setAberto(false)}>
        <Pressable style={estilos.fundo} onPress={() => setAberto(false)}>
          <View style={estilos.folha}>
            <Text style={estilos.folhaTitulo}>{label}</Text>
            <FlatList
              data={[{ value: "", label: placeholder }, ...options]}
              keyExtractor={(item) => item.value}
              style={estilos.lista}
              renderItem={({ item }) => {
                const ativo = item.value === (value ?? "");
                return (
                  <Pressable
                    style={({ pressed }) => [estilos.opcao, ativo && estilos.opcaoAtiva, pressed && estilos.opcaoPressionada]}
                    onPress={() => {
                      onChange(item.value === "" ? undefined : item.value);
                      setAberto(false);
                    }}
                  >
                    <Text style={[estilos.opcaoTexto, ativo && estilos.opcaoTextoAtivo]}>{item.label}</Text>
                  </Pressable>
                );
              }}
            />
          </View>
        </Pressable>
      </Modal>
    </View>
  );
}

const estilos = StyleSheet.create({
  campo: {
    gap: espaco[1]
  },
  label: {
    fontSize: texto.xs,
    fontWeight: peso.medio,
    color: cores.textoSuave
  },
  controle: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    height: 44,
    paddingHorizontal: espaco[3],
    borderWidth: 1,
    borderColor: cores.borda,
    borderRadius: raio.sm,
    backgroundColor: cores.superficie
  },
  controleDesabilitado: {
    opacity: 0.5
  },
  controlePressionado: {
    borderColor: cores.marcaClara,
    backgroundColor: cores.superficieSutil
  },
  valorTexto: {
    flex: 1,
    fontSize: texto.sm,
    color: cores.texto
  },
  placeholder: {
    color: cores.textoSuave
  },
  seta: {
    color: cores.textoSuave,
    marginLeft: espaco[2]
  },
  fundo: {
    flex: 1,
    backgroundColor: "rgba(21,26,41,0.45)",
    justifyContent: "flex-end"
  },
  folha: {
    maxHeight: "70%",
    backgroundColor: cores.superficie,
    borderTopLeftRadius: raio.md,
    borderTopRightRadius: raio.md,
    padding: espaco[4],
    gap: espaco[2]
  },
  folhaTitulo: {
    fontSize: texto.md,
    fontWeight: peso.forte,
    color: cores.azul900,
    marginBottom: espaco[2]
  },
  lista: {
    flexGrow: 0
  },
  opcao: {
    paddingVertical: espaco[3],
    paddingHorizontal: espaco[2],
    borderRadius: raio.sm
  },
  opcaoAtiva: {
    backgroundColor: cores.azul100
  },
  opcaoPressionada: {
    backgroundColor: cores.neutro100
  },
  opcaoTexto: {
    fontSize: texto.md,
    color: cores.texto
  },
  opcaoTextoAtivo: {
    color: cores.marca,
    fontWeight: peso.medio
  }
});
