import { useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import type { EstadoAcao } from "../../application/useAcoesRecomendadas";
import { nivelDeRisco } from "../../domain/severidade";
import type { Lead } from "../../domain/types";
import { vinCurto } from "../formatadores";
import { ROTULO_ACAO } from "../rotulos";
import { corDoNivel, cores, espaco, peso, raio, texto } from "../theme";
import BotaoCopiar from "./BotaoCopiar";
import EstadoErro from "./EstadoErro";

export interface AcaoPrioritariaProps {
  lead?: Lead;
  concessionaria: string;
  acao?: EstadoAcao;
  onCarregar: (vin: string) => void;
  onTentarNovamente: (vin: string) => void;
}

export default function AcaoPrioritaria({
  lead,
  concessionaria,
  acao,
  onCarregar,
  onTentarNovamente
}: AcaoPrioritariaProps) {
  const vin = lead?.vin;

  useEffect(() => {
    if (vin) onCarregar(vin);
  }, [vin, onCarregar]);

  if (!lead) return null;

  const nivel = nivelDeRisco(lead.score);
  const { cor, fundo } = corDoNivel(nivel);
  const percentual = Math.round(lead.score * 100);

  return (
    <View style={estilos.card}>
      <View style={estilos.topo}>
        <Text style={estilos.titulo}>Ação prioritária agora</Text>
        <View style={[estilos.selo, { backgroundColor: fundo }]}>
          <Text style={[estilos.seloTexto, { color: cor }]}>{percentual}% de risco</Text>
        </View>
      </View>

      <View style={estilos.veiculo}>
        <Text style={estilos.modelo}>{lead.modelo}</Text>
        <Text style={estilos.vin}>VIN {vinCurto(lead.vin)}</Text>
        <Text style={estilos.dealer}>{concessionaria}</Text>
      </View>

      <Text style={estilos.motivo}>{lead.motivo}</Text>

      {!acao || acao.loading ? (
        <Text style={estilos.carregando}>Buscando ação recomendada…</Text>
      ) : acao.error ? (
        <EstadoErro mensagem={acao.error.message} onTentarNovamente={() => onTentarNovamente(lead.vin)} />
      ) : acao.data ? (
        <View style={estilos.acao}>
          <View style={[estilos.seloAcao, { backgroundColor: cor }]}>
            <Text style={estilos.seloAcaoTexto}>{ROTULO_ACAO[acao.data.acao]}</Text>
          </View>
          <Text style={estilos.mensagem}>{acao.data.mensagem}</Text>
          <BotaoCopiar texto={acao.data.mensagem} />
        </View>
      ) : null}
    </View>
  );
}

const estilos = StyleSheet.create({
  card: {
    gap: espaco[3],
    padding: espaco[4],
    borderWidth: 1,
    borderColor: cores.borda,
    borderLeftWidth: 4,
    borderLeftColor: cores.riscoAlto,
    borderRadius: raio.sm,
    backgroundColor: cores.superficieSutil
  },
  topo: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    justifyContent: "space-between",
    gap: espaco[2]
  },
  titulo: {
    fontSize: texto.xs,
    fontWeight: peso.forte,
    letterSpacing: 0.5,
    textTransform: "uppercase",
    color: cores.riscoAlto
  },
  selo: {
    paddingHorizontal: espaco[2],
    paddingVertical: espaco[0],
    borderRadius: raio.pilula
  },
  seloTexto: {
    fontSize: texto.xs,
    fontWeight: peso.forte
  },
  veiculo: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "baseline",
    gap: espaco[3]
  },
  modelo: {
    fontSize: texto.lg,
    fontWeight: peso.forte,
    color: cores.azul900
  },
  vin: {
    fontFamily: "monospace",
    fontSize: texto["2xs"],
    color: cores.textoSuave
  },
  dealer: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  motivo: {
    fontSize: texto.md,
    color: cores.texto
  },
  carregando: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  acao: {
    gap: espaco[2],
    alignItems: "flex-start"
  },
  seloAcao: {
    paddingHorizontal: espaco[3],
    paddingVertical: espaco[0],
    borderRadius: raio.pilula
  },
  seloAcaoTexto: {
    fontSize: texto["2xs"],
    fontWeight: peso.forte,
    letterSpacing: 0.5,
    textTransform: "uppercase",
    color: cores.branco
  },
  mensagem: {
    padding: espaco[3],
    borderLeftWidth: 3,
    borderLeftColor: cores.marcaClara,
    borderRadius: raio.sm,
    backgroundColor: cores.superficie,
    fontSize: texto.md,
    color: cores.texto
  }
});
