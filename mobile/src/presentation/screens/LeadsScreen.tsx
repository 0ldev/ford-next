import { useMemo, useState } from "react";
import { FlatList, LayoutAnimation, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useFiltros } from "../../application/FiltrosContext";
import { useAcoesRecomendadas } from "../../application/useAcoesRecomendadas";
import { useLeads } from "../../application/useLeads";
import { encontrarLeadPrioritario } from "../../domain/leads";
import { LIMIAR_ALTO, LIMIAR_MEDIO } from "../../domain/severidade";
import { rotuloDaConcessionaria } from "../../infrastructure/mockData";
import AcaoPrioritaria from "../components/AcaoPrioritaria";
import Cabecalho from "../components/Cabecalho";
import EstadoErro from "../components/EstadoErro";
import LeadCard from "../components/LeadCard";
import Selecao, { type OpcaoSelecao } from "../components/Selecao";
import { cores, espaco, peso, raio, texto } from "../theme";

type Ordem = "asc" | "desc";
type FaixaScore = "medio" | "alto";

const CAPACIDADE_PADRAO = 50;
const CAPACIDADE_MAXIMA = 500;

const PISO_FAIXA: Record<FaixaScore, number> = {
  medio: LIMIAR_MEDIO,
  alto: LIMIAR_ALTO
};

const TETO_FAIXA: Partial<Record<FaixaScore, number>> = {
  medio: LIMIAR_ALTO
};

const OPCOES_FAIXA: OpcaoSelecao[] = [
  { value: "medio", label: `Risco médio (${Math.round(LIMIAR_MEDIO * 100)}% a ${Math.round(LIMIAR_ALTO * 100) - 1}%)` },
  { value: "alto", label: `Risco alto (≥ ${Math.round(LIMIAR_ALTO * 100)}%)` }
];

export default function LeadsScreen() {
  const { filtros } = useFiltros();
  const concessionaria = filtros.concessionaria;

  const [ordem, setOrdem] = useState<Ordem>("desc");
  const [faixa, setFaixa] = useState<FaixaScore | undefined>(undefined);
  const [pagina, setPagina] = useState(1);
  const [capacidadeTexto, setCapacidadeTexto] = useState(String(CAPACIDADE_PADRAO));
  const [expandidos, setExpandidos] = useState<string[]>([]);

  const capacidade = Math.min(CAPACIDADE_MAXIMA, Math.max(1, Math.trunc(Number(capacidadeTexto)) || CAPACIDADE_PADRAO));

  const piso = faixa ? PISO_FAIXA[faixa] : undefined;
  const teto = faixa ? TETO_FAIXA[faixa] : undefined;
  const { data, loading, error, recarregar } = useLeads({
    concessionaria,
    scoreMinimo: piso,
    scoreMaximo: teto,
    pagina,
    tamanhoPagina: capacidade
  });
  const { acoes, carregar, recarregar: recarregarAcao } = useAcoesRecomendadas();

  const [recorteAnterior, setRecorteAnterior] = useState([concessionaria, faixa, capacidade]);
  if (
    recorteAnterior[0] !== concessionaria ||
    recorteAnterior[1] !== faixa ||
    recorteAnterior[2] !== capacidade
  ) {
    setRecorteAnterior([concessionaria, faixa, capacidade]);
    setPagina(1);
  }

  const total = data?.total ?? 0;
  const tamanhoPagina = data?.tamanhoPagina ?? CAPACIDADE_PADRAO;
  const totalPaginas = Math.max(1, Math.ceil(total / tamanhoPagina));

  const leads = useMemo(() => {
    const lista = data?.leads ?? [];
    return [...lista].sort((a, b) => (ordem === "desc" ? b.prioridade - a.prioridade : a.prioridade - b.prioridade));
  }, [data, ordem]);

  const leadPrioritario = useMemo(() => encontrarLeadPrioritario(leads), [leads]);

  const alternarLinha = (vin: string) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandidos((atual) => (atual.includes(vin) ? atual.filter((item) => item !== vin) : [...atual, vin]));
    carregar(vin);
  };

  return (
    <View style={estilos.tela}>
      <Cabecalho titulo="Leads" subtitulo="Fila priorizada de contato por risco de evasão." mostrarFiltros />

      {error ? (
        <View style={estilos.estado}>
          <EstadoErro mensagem={error.message} onTentarNovamente={recarregar} />
        </View>
      ) : loading ? (
        <View style={estilos.estado}>
          <Text style={estilos.placeholder}>Carregando leads…</Text>
        </View>
      ) : (
        <FlatList
          data={leads}
          keyExtractor={(item) => item.vin}
          contentContainerStyle={estilos.conteudo}
          ListHeaderComponent={
            <View style={estilos.cabecalhoLista}>
              <AcaoPrioritaria
                lead={leadPrioritario}
                concessionaria={leadPrioritario ? rotuloDaConcessionaria(leadPrioritario.dealerCode) : ""}
                acao={leadPrioritario ? acoes[leadPrioritario.vin] : undefined}
                onCarregar={carregar}
                onTentarNovamente={recarregarAcao}
              />

              <View style={estilos.controles}>
                <Selecao
                  label="Faixa de risco"
                  options={OPCOES_FAIXA}
                  value={faixa}
                  onChange={(valor) => setFaixa(valor as FaixaScore | undefined)}
                  placeholder="Todos os scores"
                />

                <View style={estilos.campoCapacidade}>
                  <Text style={estilos.labelCapacidade}>Contatos possíveis esta semana</Text>
                  <TextInput
                    style={estilos.inputCapacidade}
                    keyboardType="number-pad"
                    value={capacidadeTexto}
                    onChangeText={setCapacidadeTexto}
                  />
                </View>

                <Pressable onPress={() => setOrdem((atual) => (atual === "desc" ? "asc" : "desc"))}>
                  <Text style={estilos.ordenar}>
                    Ordenar por prioridade {ordem === "desc" ? "▼ maior primeiro" : "▲ menor primeiro"}
                  </Text>
                </Pressable>

                <Text style={estilos.contagem}>
                  {total} {total === 1 ? "lead" : "leads"}
                  {faixa ? " nesta faixa" : " na fila"}
                </Text>
              </View>
            </View>
          }
          renderItem={({ item }) => (
            <LeadCard
              lead={item}
              expandido={expandidos.includes(item.vin)}
              onAlternar={() => alternarLinha(item.vin)}
              acao={acoes[item.vin]}
              onTentarNovamente={() => recarregarAcao(item.vin)}
            />
          )}
          ItemSeparatorComponent={() => <View style={{ height: espaco[3] }} />}
          ListEmptyComponent={<Text style={estilos.placeholder}>Nenhum lead encontrado para este filtro.</Text>}
          ListFooterComponent={
            totalPaginas > 1 ? (
              <View style={estilos.paginacao}>
                <Pressable
                  style={({ pressed }) => [
                    estilos.botaoPaginacao,
                    pagina <= 1 && estilos.botaoDesabilitado,
                    pressed && pagina > 1 && estilos.botaoPressionado
                  ]}
                  onPress={() => setPagina((atual) => atual - 1)}
                  disabled={pagina <= 1}
                >
                  <Text style={[estilos.botaoPaginacaoTexto, pagina <= 1 && estilos.textoDesabilitado]}>← Anterior</Text>
                </Pressable>
                <Text style={estilos.paginacaoTexto}>
                  Página {pagina} de {totalPaginas}
                </Text>
                <Pressable
                  style={({ pressed }) => [
                    estilos.botaoPaginacao,
                    pagina >= totalPaginas && estilos.botaoDesabilitado,
                    pressed && pagina < totalPaginas && estilos.botaoPressionado
                  ]}
                  onPress={() => setPagina((atual) => atual + 1)}
                  disabled={pagina >= totalPaginas}
                >
                  <Text style={[estilos.botaoPaginacaoTexto, pagina >= totalPaginas && estilos.textoDesabilitado]}>
                    Próxima →
                  </Text>
                </Pressable>
              </View>
            ) : null
          }
        />
      )}
    </View>
  );
}

const estilos = StyleSheet.create({
  tela: {
    flex: 1,
    backgroundColor: cores.fundo
  },
  estado: {
    padding: espaco[5]
  },
  placeholder: {
    fontSize: texto.md,
    color: cores.textoSuave,
    textAlign: "center",
    paddingVertical: espaco[4]
  },
  conteudo: {
    padding: espaco[4],
    gap: espaco[3]
  },
  cabecalhoLista: {
    gap: espaco[4],
    marginBottom: espaco[2]
  },
  controles: {
    gap: espaco[3]
  },
  campoCapacidade: {
    gap: espaco[1]
  },
  labelCapacidade: {
    fontSize: texto.xs,
    fontWeight: peso.medio,
    color: cores.textoSuave
  },
  inputCapacidade: {
    height: 44,
    paddingHorizontal: espaco[3],
    borderWidth: 1,
    borderColor: cores.borda,
    borderRadius: raio.sm,
    backgroundColor: cores.superficie,
    fontSize: texto.sm,
    color: cores.texto
  },
  ordenar: {
    fontSize: texto.sm,
    fontWeight: peso.medio,
    color: cores.marca
  },
  contagem: {
    fontSize: texto.sm,
    color: cores.textoSuave
  },
  paginacao: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: espaco[4],
    paddingVertical: espaco[4]
  },
  botaoPaginacao: {
    height: 40,
    paddingHorizontal: espaco[4],
    borderWidth: 1,
    borderColor: cores.marca,
    borderRadius: raio.sm,
    alignItems: "center",
    justifyContent: "center"
  },
  botaoDesabilitado: {
    borderColor: cores.borda
  },
  botaoPressionado: {
    backgroundColor: cores.azul100
  },
  botaoPaginacaoTexto: {
    fontSize: texto.sm,
    fontWeight: peso.medio,
    color: cores.marca
  },
  textoDesabilitado: {
    color: cores.neutro400
  },
  paginacaoTexto: {
    fontSize: texto.sm,
    color: cores.textoSuave
  }
});
