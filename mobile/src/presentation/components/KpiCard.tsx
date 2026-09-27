import { StyleSheet, Text, View } from "react-native";
import { formatarComCasas } from "../formatadores";
import { cores, espaco, peso, raio, texto } from "../theme";
import EsqueletoPulsante from "./EsqueletoPulsante";
import EstadoErro from "./EstadoErro";

export interface ComparacaoKpi {
  base: number;
  rotuloBase: string;
}

export interface KpiCardProps {
  label: string;
  valor?: number | null;
  valorTexto?: string | null;
  unidade?: string;
  casasDecimais?: number;
  contexto?: string;
  comparacao?: ComparacaoKpi;
  loading?: boolean;
  erro?: string | null;
  onTentarNovamente?: () => void;
}

export default function KpiCard({
  label,
  valor,
  valorTexto,
  unidade = "%",
  casasDecimais = 1,
  contexto,
  comparacao,
  loading = false,
  erro = null,
  onTentarNovamente
}: KpiCardProps) {
  const temValor = typeof valor === "number" && Number.isFinite(valor);
  const temValorTexto = !temValor && typeof valorTexto === "string" && valorTexto !== "";
  const temConteudo = temValor || temValorTexto;

  const diferenca = temValor && comparacao ? valor - comparacao.base : null;
  const sentido = diferenca === null ? null : diferenca >= 0 ? "acima" : "abaixo";

  const valorFormatado = temValor ? formatarComCasas(valor, casasDecimais) : null;

  return (
    <View style={estilos.card}>
      <Text style={estilos.label}>{label}</Text>

      {erro ? (
        <EstadoErro mensagem={erro} onTentarNovamente={onTentarNovamente} />
      ) : loading || !temConteudo ? (
        <EsqueletoPulsante style={estilos.skeleton} />
      ) : temValorTexto ? (
        <Text style={estilos.valorTexto}>{valorTexto}</Text>
      ) : (
        <Text style={estilos.valor}>
          {valorFormatado}
          <Text style={estilos.unidade}>{unidade}</Text>
        </Text>
      )}

      {comparacao && diferenca !== null && sentido && !erro && !loading && (
        <Text style={[estilos.comparacao, { color: sentido === "acima" ? cores.verdePositivo : cores.riscoAlto }]}>
          {sentido === "acima" ? "▲ " : "▼ "}
          {formatarComCasas(Math.abs(diferenca))} p.p. {sentido} da {comparacao.rotuloBase} (
          {formatarComCasas(comparacao.base)}%)
        </Text>
      )}

      {contexto && !erro && !loading && <Text style={estilos.contexto}>{contexto}</Text>}
    </View>
  );
}

const estilos = StyleSheet.create({
  card: {
    minHeight: 132,
    justifyContent: "center",
    gap: espaco[2],
    padding: espaco[4],
    borderWidth: 1,
    borderColor: cores.borda,
    borderLeftWidth: 4,
    borderLeftColor: cores.marca,
    borderRadius: raio.sm,
    backgroundColor: cores.superficie
  },
  label: {
    fontSize: texto.xs,
    fontWeight: peso.forte,
    letterSpacing: 0.5,
    textTransform: "uppercase",
    color: cores.textoSuave
  },
  valor: {
    fontSize: texto.kpi,
    fontWeight: peso.forte,
    letterSpacing: -0.5,
    color: cores.azul900,
    fontVariant: ["tabular-nums"]
  },
  valorTexto: {
    fontSize: texto.xl,
    fontWeight: peso.forte,
    color: cores.azul800
  },
  unidade: {
    fontSize: texto.lg,
    fontWeight: peso.medio,
    color: cores.marcaClara
  },
  contexto: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  comparacao: {
    fontSize: texto.sm,
    fontWeight: peso.medio
  },
  skeleton: {
    height: texto.kpi + 4,
    width: "60%",
    minWidth: 140,
    borderRadius: raio.sm
  }
});
