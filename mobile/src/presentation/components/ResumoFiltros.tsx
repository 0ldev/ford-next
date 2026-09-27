import { StyleSheet, Text, View } from "react-native";
import { FAIXAS_IDADE, rotuloDaConcessionaria } from "../../infrastructure/mockData";
import type { VinShareFiltros } from "../../domain/types";
import { formatarDataBR } from "../formatadores";
import { cores, espaco, peso, raio, texto } from "../theme";

export interface ResumoFiltrosProps {
  filtros: VinShareFiltros;
}

function rotuloDaFaixa(valor: string): string {
  return FAIXAS_IDADE.find((faixa) => faixa.value === valor)?.label ?? valor;
}

function trechoDePeriodo(inicio?: string, fim?: string): string | null {
  if (inicio && fim) return `de ${formatarDataBR(inicio)} a ${formatarDataBR(fim)}`;
  if (inicio) return `a partir de ${formatarDataBR(inicio)}`;
  if (fim) return `até ${formatarDataBR(fim)}`;
  return null;
}

function juntar(trechos: string[]): string {
  if (trechos.length === 1) return trechos[0];
  return `${trechos.slice(0, -1).join(", ")} e ${trechos[trechos.length - 1]}`;
}

export function descreverFiltros(filtros: VinShareFiltros): string {
  const trechos: string[] = [];

  if (filtros.concessionaria) {
    trechos.push(`concessionária ${rotuloDaConcessionaria(filtros.concessionaria)}`);
  }
  if (filtros.modelo) trechos.push(`modelo ${filtros.modelo}`);
  if (filtros.faixaIdade) trechos.push(`veículos de ${rotuloDaFaixa(filtros.faixaIdade)}`);
  if (filtros.tipoServico) trechos.push(`serviços de ${filtros.tipoServico.toLowerCase()}`);

  const periodo = trechoDePeriodo(filtros.periodoInicio, filtros.periodoFim);
  if (periodo) trechos.push(periodo);

  if (trechos.length === 0) return "todos os veículos elegíveis da rede, em todo o período";

  return juntar(trechos);
}

export default function ResumoFiltros({ filtros }: ResumoFiltrosProps) {
  return (
    <View style={estilos.container}>
      <Text style={estilos.rotulo}>Mostrando</Text>
      <Text style={estilos.texto}>{descreverFiltros(filtros)}</Text>
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    borderLeftWidth: 3,
    borderLeftColor: cores.marcaClara,
    borderRadius: raio.sm,
    backgroundColor: cores.azul100,
    paddingVertical: espaco[3],
    paddingHorizontal: espaco[4],
    gap: espaco[1]
  },
  rotulo: {
    fontSize: texto["2xs"],
    fontWeight: peso.forte,
    letterSpacing: 0.5,
    textTransform: "uppercase",
    color: cores.marca
  },
  texto: {
    fontSize: texto.md,
    color: cores.texto
  }
});
