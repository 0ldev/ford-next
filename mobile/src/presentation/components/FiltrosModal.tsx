import { useMemo } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFiltros } from "../../application/FiltrosContext";
import { formatarCompetenciaLonga } from "../../domain/competencia";
import { FAIXAS_IDADE, rotuloDaConcessionaria } from "../../infrastructure/mockData";
import { formatarDataBR } from "../formatadores";
import { competenciasDoPeriodo, primeiroDiaDoMes, ultimoDiaDoMes } from "../periodo";
import { cores, espaco, peso, raio, texto } from "../theme";
import ResumoFiltros from "./ResumoFiltros";
import Selecao, { type OpcaoSelecao } from "./Selecao";

export interface FiltrosModalProps {
  onFechar: () => void;
}

export default function FiltrosModal({ onFechar }: FiltrosModalProps) {
  const { filtros, atualizarFiltros, limparFiltros, catalogo } = useFiltros();

  const opcoesConcessionaria: OpcaoSelecao[] = useMemo(
    () =>
      (catalogo?.concessionarias ?? []).map((dealerCode) => {
        const nome = rotuloDaConcessionaria(dealerCode);
        return { value: dealerCode, label: nome === dealerCode ? dealerCode : `${dealerCode} — ${nome}` };
      }),
    [catalogo]
  );

  const opcoesModelo: OpcaoSelecao[] = useMemo(
    () => (catalogo?.modelos ?? []).map((modelo) => ({ value: modelo, label: modelo })),
    [catalogo]
  );

  const opcoesTipoServico: OpcaoSelecao[] = useMemo(
    () => (catalogo?.tiposServico ?? []).map((tipo) => ({ value: tipo, label: tipo })),
    [catalogo]
  );

  const opcoesFaixaIdade: OpcaoSelecao[] = FAIXAS_IDADE.map((faixa) => ({ value: faixa.value, label: faixa.label }));

  const opcoesPeriodo: OpcaoSelecao[] = useMemo(() => {
    const competencias = competenciasDoPeriodo(
      catalogo?.periodoDisponivel?.inicio,
      catalogo?.periodoDisponivel?.fim
    );
    return competencias.map((competencia) => ({ value: competencia, label: formatarCompetenciaLonga(competencia) }));
  }, [catalogo]);

  const algumFiltroAtivo = Object.values(filtros).some((valor) => valor !== undefined && valor !== "");

  return (
    <View style={estilos.container}>
      <View style={estilos.cabecalho}>
        <Text style={estilos.titulo}>Filtros</Text>
        <Pressable onPress={onFechar}>
          <Text style={estilos.fechar}>Fechar</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={estilos.conteudo}>
        <Selecao
          label="Concessionária"
          options={opcoesConcessionaria}
          value={filtros.concessionaria}
          onChange={(concessionaria) => atualizarFiltros({ concessionaria })}
          placeholder="Todas"
        />

        <Selecao
          label="Modelo"
          options={opcoesModelo}
          value={filtros.modelo}
          onChange={(modelo) => atualizarFiltros({ modelo })}
          placeholder="Todos"
        />

        <Selecao
          label="Idade do veículo"
          options={opcoesFaixaIdade}
          value={filtros.faixaIdade}
          onChange={(faixaIdade) => atualizarFiltros({ faixaIdade })}
          placeholder="Todas as idades"
        />

        <Selecao
          label="Tipo de serviço"
          options={opcoesTipoServico}
          value={filtros.tipoServico}
          onChange={(tipoServico) => atualizarFiltros({ tipoServico })}
          placeholder="Todos"
        />

        <Selecao
          label="Período — início"
          options={opcoesPeriodo}
          value={filtros.periodoInicio?.slice(0, 7)}
          onChange={(competencia) =>
            atualizarFiltros({ periodoInicio: competencia ? primeiroDiaDoMes(competencia) : undefined })
          }
          placeholder="Sem início definido"
        />

        <Selecao
          label="Período — fim"
          options={opcoesPeriodo}
          value={filtros.periodoFim?.slice(0, 7)}
          onChange={(competencia) =>
            atualizarFiltros({ periodoFim: competencia ? ultimoDiaDoMes(competencia) : undefined })
          }
          placeholder="Sem fim definido"
        />

        {catalogo?.periodoDisponivel && (
          <Text style={estilos.ajuda}>
            Dados disponíveis de {formatarDataBR(catalogo.periodoDisponivel.inicio)} a{" "}
            {formatarDataBR(catalogo.periodoDisponivel.fim)}.
          </Text>
        )}

        <ResumoFiltros filtros={filtros} />

        <Pressable
          style={({ pressed }) => [
            estilos.botaoLimpar,
            !algumFiltroAtivo && estilos.botaoDesabilitado,
            pressed && algumFiltroAtivo && estilos.botaoLimparPressionado
          ]}
          onPress={limparFiltros}
          disabled={!algumFiltroAtivo}
        >
          <Text style={[estilos.botaoLimparTexto, !algumFiltroAtivo && estilos.botaoTextoDesabilitado]}>
            Limpar filtros
          </Text>
        </Pressable>

        <Pressable
          style={({ pressed }) => [estilos.botaoAplicar, pressed && estilos.botaoAplicarPressionado]}
          onPress={onFechar}
        >
          <Text style={estilos.botaoAplicarTexto}>Aplicar e voltar</Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: cores.fundo
  },
  cabecalho: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: espaco[5],
    paddingTop: espaco[6],
    paddingBottom: espaco[4],
    borderBottomWidth: 1,
    borderBottomColor: cores.borda,
    backgroundColor: cores.superficie
  },
  titulo: {
    fontSize: texto.xl,
    fontWeight: peso.forte,
    color: cores.azul900
  },
  fechar: {
    fontSize: texto.md,
    color: cores.marcaClara,
    fontWeight: peso.medio
  },
  conteudo: {
    padding: espaco[5],
    gap: espaco[4]
  },
  ajuda: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  botaoLimpar: {
    height: 44,
    borderWidth: 1,
    borderColor: cores.marca,
    borderRadius: raio.sm,
    alignItems: "center",
    justifyContent: "center"
  },
  botaoDesabilitado: {
    borderColor: cores.borda
  },
  botaoLimparPressionado: {
    backgroundColor: cores.azul100
  },
  botaoLimparTexto: {
    fontSize: texto.sm,
    fontWeight: peso.medio,
    color: cores.marca
  },
  botaoTextoDesabilitado: {
    color: cores.neutro400
  },
  botaoAplicar: {
    height: 48,
    borderRadius: raio.sm,
    backgroundColor: cores.marca,
    alignItems: "center",
    justifyContent: "center"
  },
  botaoAplicarPressionado: {
    backgroundColor: cores.azul600
  },
  botaoAplicarTexto: {
    fontSize: texto.md,
    fontWeight: peso.forte,
    color: cores.branco
  }
});
