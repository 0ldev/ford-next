import { Pressable, StyleSheet, Text, View } from "react-native";
import type { EstadoAcao } from "../../application/useAcoesRecomendadas";
import { nivelDeRisco } from "../../domain/severidade";
import type { Lead } from "../../domain/types";
import { rotuloDaConcessionaria } from "../../infrastructure/mockData";
import { encurtarVin } from "../formatadores";
import { ROTULO_ACAO } from "../rotulos";
import { corDoNivel, cores, espaco, peso, raio, texto } from "../theme";
import BotaoCopiar from "./BotaoCopiar";
import EstadoErro from "./EstadoErro";

export interface LeadCardProps {
  lead: Lead;
  expandido: boolean;
  onAlternar: () => void;
  acao?: EstadoAcao;
  onTentarNovamente: () => void;
}

export default function LeadCard({ lead, expandido, onAlternar, acao, onTentarNovamente }: LeadCardProps) {
  const nivel = nivelDeRisco(lead.score);
  const { cor, fundo } = corDoNivel(nivel);

  return (
    <View style={[estilos.card, expandido && estilos.cardExpandido]}>
      <Pressable
        style={({ pressed }) => [estilos.cabecalho, pressed && estilos.cabecalhoPressionado]}
        onPress={onAlternar}
      >
        <View style={estilos.cabecalhoTexto}>
          <View style={estilos.linhaTopo}>
            <Text style={estilos.modelo}>{lead.modelo}</Text>
            <View style={[estilos.score, { backgroundColor: fundo }]}>
              <Text style={[estilos.scoreTexto, { color: cor }]}>{Math.round(lead.score * 100)}%</Text>
            </View>
          </View>
          <Text style={estilos.dealer}>{rotuloDaConcessionaria(lead.dealerCode)}</Text>
          <Text style={estilos.vin}>{encurtarVin(lead.vin)}</Text>
          <Text style={estilos.motivo} numberOfLines={expandido ? undefined : 2}>
            {lead.motivo}
          </Text>
          <Text style={estilos.prioridade}>Prioridade {Math.round(lead.prioridade * 100)}%</Text>
        </View>
        <Text style={estilos.expandirIcone}>{expandido ? "−" : "+"}</Text>
      </Pressable>

      {expandido && (
        <View style={estilos.detalhe}>
          <Text style={estilos.detalheTitulo}>Ação recomendada</Text>

          {!acao || acao.loading ? (
            <Text style={estilos.carregando}>Buscando ação recomendada…</Text>
          ) : acao.error ? (
            <EstadoErro mensagem={acao.error.message} onTentarNovamente={onTentarNovamente} />
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
      )}
    </View>
  );
}

const estilos = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderColor: cores.borda,
    borderRadius: raio.sm,
    backgroundColor: cores.superficie,
    overflow: "hidden"
  },
  cardExpandido: {
    borderColor: cores.marcaClara
  },
  cabecalho: {
    flexDirection: "row",
    alignItems: "flex-start",
    padding: espaco[4],
    gap: espaco[3]
  },
  cabecalhoPressionado: {
    backgroundColor: cores.superficieSutil
  },
  cabecalhoTexto: {
    flex: 1,
    gap: espaco[1]
  },
  linhaTopo: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  modelo: {
    fontSize: texto.md,
    fontWeight: peso.forte,
    color: cores.azul900
  },
  score: {
    paddingHorizontal: espaco[2],
    borderRadius: raio.pilula
  },
  scoreTexto: {
    fontSize: texto.sm,
    fontWeight: peso.forte
  },
  dealer: {
    fontSize: texto.sm,
    color: cores.texto
  },
  vin: {
    fontFamily: "monospace",
    fontSize: texto["2xs"],
    color: cores.textoSuave
  },
  motivo: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  prioridade: {
    fontSize: texto["2xs"],
    fontWeight: peso.medio,
    color: cores.marca,
    marginTop: espaco[1]
  },
  expandirIcone: {
    fontSize: texto.lg,
    color: cores.marca,
    width: 24,
    textAlign: "center"
  },
  detalhe: {
    borderTopWidth: 1,
    borderTopColor: cores.neutro200,
    backgroundColor: cores.azul100,
    padding: espaco[4],
    gap: espaco[2]
  },
  detalheTitulo: {
    fontSize: texto["2xs"],
    fontWeight: peso.forte,
    letterSpacing: 0.5,
    textTransform: "uppercase",
    color: cores.textoSuave
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
