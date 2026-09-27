import { useState } from "react";
import { StyleSheet, Text, View, type LayoutChangeEvent } from "react-native";
import Svg, { Circle, Line, Polyline } from "react-native-svg";
import { formatarCompetenciaCurtaMes } from "../../../domain/competencia";
import { cores } from "../../theme";

export interface PontoGraficoLinha {
  data: string;
  [serie: string]: string | number;
}

export interface LinhaTendenciaChartProps {
  linhas: PontoGraficoLinha[];
  series: string[];
  cores: string[];
  altura?: number;
}

const PADDING_ESQUERDA = 34;
const PADDING_DIREITA = 8;
const PADDING_TOPO = 12;
const PADDING_BASE = 22;

export default function LinhaTendenciaChart({ linhas, series, cores: coresSeries, altura = 220 }: LinhaTendenciaChartProps) {
  const [largura, setLargura] = useState(0);

  const aoMedir = (evento: LayoutChangeEvent) => {
    setLargura(evento.nativeEvent.layout.width);
  };

  const valores = series.flatMap((serie) => linhas.map((linha) => Number(linha[serie]) || 0));
  const maiorValor = Math.max(10, ...valores);
  const tetoY = Math.ceil((maiorValor * 1.15) / 10) * 10;

  const innerWidth = Math.max(0, largura - PADDING_ESQUERDA - PADDING_DIREITA);
  const innerHeight = altura - PADDING_TOPO - PADDING_BASE;

  const x = (indice: number) =>
    PADDING_ESQUERDA + (linhas.length > 1 ? (indice / (linhas.length - 1)) * innerWidth : innerWidth / 2);
  const y = (valor: number) => PADDING_TOPO + innerHeight - (valor / tetoY) * innerHeight;

  const gridFracoes = [0, 0.25, 0.5, 0.75, 1];
  const passoRotulo = Math.max(1, Math.ceil(linhas.length / 6));

  return (
    <View style={estilos.wrapper} onLayout={aoMedir}>
      {largura > 0 && (
        <Svg width={largura} height={altura}>
          {gridFracoes.map((fracao) => (
            <Line
              key={fracao}
              x1={PADDING_ESQUERDA}
              x2={largura - PADDING_DIREITA}
              y1={y(tetoY * fracao)}
              y2={y(tetoY * fracao)}
              stroke={cores.neutro200}
              strokeWidth={1}
            />
          ))}

          {series.map((serie, indiceSerie) => {
            const pontos = linhas.map((linha, indice) => `${x(indice)},${y(Number(linha[serie]) || 0)}`).join(" ");
            return (
              <Polyline
                key={serie}
                points={pontos}
                fill="none"
                stroke={coresSeries[indiceSerie % coresSeries.length]}
                strokeWidth={2.5}
              />
            );
          })}

          {series.map((serie, indiceSerie) => {
            const ultimo = linhas[linhas.length - 1];
            if (!ultimo) return null;
            return (
              <Circle
                key={`ponto-${serie}`}
                cx={x(linhas.length - 1)}
                cy={y(Number(ultimo[serie]) || 0)}
                r={3.5}
                fill={coresSeries[indiceSerie % coresSeries.length]}
              />
            );
          })}
        </Svg>
      )}

      <View pointerEvents="none" style={StyleSheet.absoluteFill}>
        {gridFracoes.map((fracao) => (
          <Text key={fracao} style={[estilos.rotuloY, { top: y(tetoY * fracao) - 7 }]}>
            {Math.round(tetoY * fracao)}%
          </Text>
        ))}
      </View>

      <View style={estilos.eixoX}>
        {linhas.map((linha, indice) =>
          indice % passoRotulo === 0 || indice === linhas.length - 1 ? (
            <Text key={linha.data} style={[estilos.rotuloX, { left: x(indice) - 16 }]}>
              {formatarCompetenciaCurtaMes(linha.data)}
            </Text>
          ) : null
        )}
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  wrapper: {
    width: "100%"
  },
  rotuloY: {
    position: "absolute",
    left: 0,
    width: PADDING_ESQUERDA - 4,
    fontSize: 9,
    textAlign: "right",
    color: cores.textoSuave
  },
  eixoX: {
    height: PADDING_BASE,
    position: "relative"
  },
  rotuloX: {
    position: "absolute",
    top: 4,
    width: 32,
    fontSize: 9,
    textAlign: "center",
    color: cores.textoSuave
  }
});
