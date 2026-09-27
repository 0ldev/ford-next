/**
 * Fonte de dados mockada.
 *
 * Enquanto os endpoints reais não existem, este módulo produz respostas com
 * a mesma forma dos tipos em `domain/types`, para que o dashboard seja
 * desenvolvido e demonstrado ponta a ponta. Os números foram calibrados
 * para lembrar o dataset real (602.788 ordens de serviço, 175.554 veículos,
 * 435 concessionárias, concentração em RANGER e KA).
 *
 * A geração é determinística (PRNG com semente fixa): recarregar a página
 * não embaralha os leads, o que evita ruído durante o desenvolvimento da UI.
 */

import type {
  AcaoRecomendada,
  AcaoTipo,
  AnomaliesResponse,
  Anomaly,
  Catalogo,
  Lead,
  LeadsFiltros,
  LeadsResponse,
  ResumoExecutivo,
  ScoreDistributionResponse,
  TrendConcessionariaFiltros,
  TrendConcessionariaResponse,
  TrendFiltros,
  TrendResponse,
  VinShareFiltros,
  VinShareResponse
} from "../domain/types";

/* ------------------------------------------------------------------ */
/* Catálogos (também usados pela barra de filtros)                     */
/* ------------------------------------------------------------------ */

export interface ConcessionariaMock {
  dealerCode: string;
  nome: string;
}

export const CONCESSIONARIAS: ConcessionariaMock[] = [
  { dealerCode: "BR0142", nome: "Ford Sorana — Campinas/SP" },
  { dealerCode: "BR0317", nome: "Ford Rodobens — Ribeirão Preto/SP" },
  { dealerCode: "BR0588", nome: "Ford Vale Sul — São José dos Campos/SP" },
  { dealerCode: "BR0731", nome: "Ford Bahia Motors — Salvador/BA" },
  { dealerCode: "BR0904", nome: "Ford Trioeste — Curitiba/PR" }
];

export const MODELOS = ["RANGER", "KA", "ECOSPORT", "TERRITORY", "MAVERICK"] as const;

/**
 * Nome de exibição de uma concessionária a partir do `dealerCode`.
 *
 * Único ponto de resolução do nome (antes duplicado em `LeadsTable.tsx` e
 * `ResumoFiltros.tsx`) — usado tanto no modo mock (nomes fictícios de
 * `CONCESSIONARIAS`) quanto com a API real: como o dataset real só tem o
 * código numérico, sem nome de concessionária, o fallback (`?? dealerCode`)
 * é o que aparece de fato fora do modo mock — comportamento esperado, não bug.
 */
export function rotuloDaConcessionaria(dealerCode: string): string {
  return CONCESSIONARIAS.find((item) => item.dealerCode === dealerCode)?.nome ?? dealerCode;
}

/**
 * Faixas de idade do veículo. Os `value` são os mesmos que o backend usará
 * no parâmetro `faixaIdade`; o `label` é só apresentação.
 */
export interface FaixaIdadeMock {
  value: string;
  label: string;
}

export const FAIXAS_IDADE: FaixaIdadeMock[] = [
  { value: "0-1", label: "0-1 anos" },
  { value: "1-2", label: "1-2 anos" },
  { value: "2-4", label: "2-4 anos" },
  { value: "4+", label: "4+ anos" }
];

export const TIPOS_SERVICO = [
  "Revisão programada",
  "Manutenção corretiva",
  "Garantia",
  "Recall",
  "Funilaria"
] as const;

/** Participação de cada modelo no volume, refletindo a concentração do dataset real. */
const PESO_MODELO: Record<string, number> = {
  RANGER: 0.57,
  KA: 0.22,
  ECOSPORT: 0.11,
  TERRITORY: 0.06,
  MAVERICK: 0.04
};

/** VIN share médio por modelo (%), base das séries e do KPI. */
const SHARE_BASE_MODELO: Record<string, number> = {
  RANGER: 42.6,
  KA: 26.9,
  ECOSPORT: 31.4,
  TERRITORY: 47.2,
  MAVERICK: 51.8
};

/** Veículos elegíveis por modelo, somando ~175 mil como no dataset real. */
const ELEGIVEIS_MODELO: Record<string, number> = {
  RANGER: 100066,
  KA: 38622,
  ECOSPORT: 19311,
  TERRITORY: 10533,
  MAVERICK: 7022
};

/* ------------------------------------------------------------------ */
/* Utilitários determinísticos                                         */
/* ------------------------------------------------------------------ */

/**
 * Avalanche da semente (splitmix32).
 *
 * O mulberry32 tem avalanche fraca no primeiro valor: sementes diferentes
 * mas próximas devolviam quase o mesmo número, o que fazia intervalos de
 * data distintos caírem no mesmo ajuste. Embaralhar a semente antes separa
 * as sequências.
 */
function misturarSemente(valor: number): number {
  let x = valor >>> 0;
  x = Math.imul(x ^ (x >>> 16), 0x21f0aaad);
  x = Math.imul(x ^ (x >>> 15), 0x735a2d97);
  return (x ^ (x >>> 15)) >>> 0;
}

/** PRNG mulberry32 — pequeno, determinístico e suficiente para dados fake. */
function criarRandom(semente: number): () => number {
  let estado = misturarSemente(semente);
  return () => {
    estado = (estado + 0x6d2b79f5) >>> 0;
    let t = estado;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Hash estável de string para semear o PRNG a partir de um texto. */
function hashTexto(texto: string): number {
  let hash = 2166136261;
  for (let i = 0; i < texto.length; i += 1) {
    hash ^= texto.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

/** VIN anonimizado: hash hexadecimal de 40 caracteres, como no dataset tratado. */
function gerarVinHash(indice: number): string {
  const random = criarRandom(hashTexto(`vin-${indice}`));
  let hex = "";
  while (hex.length < 40) {
    hex += Math.floor(random() * 0xffffffff)
      .toString(16)
      .padStart(8, "0");
  }
  return hex.slice(0, 40);
}

function arredondar(valor: number, casas = 1): number {
  const fator = 10 ** casas;
  return Math.round(valor * fator) / fator;
}

function limitar(valor: number, minimo: number, maximo: number): number {
  return Math.min(maximo, Math.max(minimo, valor));
}

/** Lista de competências "YYYY-MM" entre início e fim, inclusive. */
function listarMeses(inicio: string, fim: string): string[] {
  const [anoInicio, mesInicio] = inicio.split("-").map(Number);
  const [anoFim, mesFim] = fim.split("-").map(Number);
  const meses: string[] = [];

  let ano = anoInicio;
  let mes = mesInicio;
  // Guarda contra intervalos invertidos ou absurdos vindos da UI.
  while ((ano < anoFim || (ano === anoFim && mes <= mesFim)) && meses.length < 120) {
    meses.push(`${ano}-${String(mes).padStart(2, "0")}`);
    mes += 1;
    if (mes > 12) {
      mes = 1;
      ano += 1;
    }
  }
  return meses;
}

const PERIODO_PADRAO_INICIO = "2025-01";
const PERIODO_PADRAO_FIM = "2026-06";

/* ------------------------------------------------------------------ */
/* GET /api/vin-share                                                  */
/* ------------------------------------------------------------------ */

/** Fatores multiplicativos por faixa de idade: carro mais velho volta menos à rede. */
const FATOR_FAIXA_IDADE: Record<string, number> = {
  "0-1": 1.58,
  "1-2": 1.29,
  "2-4": 0.97,
  "4+": 0.59
};

const FATOR_TIPO_SERVICO: Record<string, number> = {
  "Revisão programada": 1.18,
  "Manutenção corretiva": 0.88,
  Garantia: 1.24,
  Recall: 1.07,
  Funilaria: 0.52
};

/**
 * Deslocamento do share conforme o período selecionado: de -5 a -3 ou de
 * +3 a +5 pontos percentuais, estável para um mesmo intervalo de datas.
 *
 * Existe para a demo refletir mudança real ao filtrar por período — na API
 * real esse efeito vem do próprio recorte temporal dos dados.
 */
function ajustePorPeriodo(inicio?: string, fim?: string): number {
  if (!inicio && !fim) return 0;

  const random = criarRandom(hashTexto(`periodo|${inicio ?? ""}|${fim ?? ""}`));
  const magnitude = 3 + random() * 2;
  const sinal = random() < 0.5 ? -1 : 1;
  return sinal * magnitude;
}

export function mockVinShare(filtros: VinShareFiltros = {}): VinShareResponse {
  const modelo = filtros.modelo;
  const shareBase = modelo ? (SHARE_BASE_MODELO[modelo] ?? 33.5) : 34.7;

  let share = shareBase;
  share *= filtros.faixaIdade ? (FATOR_FAIXA_IDADE[filtros.faixaIdade] ?? 1) : 1;
  share *= filtros.tipoServico ? (FATOR_TIPO_SERVICO[filtros.tipoServico] ?? 1) : 1;

  // Cada concessionária puxa o indicador para um lado, de forma estável.
  if (filtros.concessionaria) {
    const random = criarRandom(hashTexto(filtros.concessionaria));
    share *= 0.78 + random() * 0.44;
  }

  share += ajustePorPeriodo(filtros.periodoInicio, filtros.periodoFim);

  const elegiveisTotais = modelo
    ? (ELEGIVEIS_MODELO[modelo] ?? 12000)
    : Object.values(ELEGIVEIS_MODELO).reduce((soma, valor) => soma + valor, 0);

  let elegiveis = elegiveisTotais;
  if (filtros.concessionaria) elegiveis = Math.round(elegiveis * 0.031);
  if (filtros.faixaIdade) elegiveis = Math.round(elegiveis * 0.34);
  if (filtros.periodoInicio || filtros.periodoFim) elegiveis = Math.round(elegiveis * 0.72);

  const vinShareEstimado = arredondar(limitar(share, 3, 92));
  const totalComServico = Math.round((elegiveis * vinShareEstimado) / 100);

  return {
    vinShareEstimado,
    totalVeiculosElegiveis: elegiveis,
    totalComServico,
    filtrosAplicados: {
      concessionaria: filtros.concessionaria ?? null,
      modelo: filtros.modelo ?? null,
      faixaIdade: filtros.faixaIdade ?? null,
      tipoServico: filtros.tipoServico ?? null,
      periodoInicio: filtros.periodoInicio ?? null,
      periodoFim: filtros.periodoFim ?? null
    }
  };
}

/* ------------------------------------------------------------------ */
/* GET /api/trend                                                      */
/* ------------------------------------------------------------------ */

export function mockTrend(filtros: TrendFiltros = {}): TrendResponse {
  const modelos = filtros.modelo && filtros.modelo.length > 0 ? filtros.modelo : [...MODELOS];
  const meses = listarMeses(
    filtros.periodoInicio ?? PERIODO_PADRAO_INICIO,
    filtros.periodoFim ?? PERIODO_PADRAO_FIM
  );

  const pontos: TrendResponse = [];
  for (const modelo of modelos) {
    const base = SHARE_BASE_MODELO[modelo] ?? 33.5;
    const random = criarRandom(hashTexto(`trend-${modelo}`));
    // Tendência de queda leve ao longo do período — o problema que o hub existe para expor.
    const inclinacao = -0.28 - random() * 0.35;

    meses.forEach((mes, indice) => {
      const sazonalidade = Math.sin((indice / 12) * Math.PI * 2) * 2.1;
      const ruido = (random() - 0.5) * 3.4;
      const valor = limitar(base + inclinacao * indice + sazonalidade + ruido, 2, 95);
      pontos.push({ data: mes, valor: arredondar(valor), categoria: modelo });
    });
  }

  return pontos;
}

/* ------------------------------------------------------------------ */
/* GET /api/trend/concessionarias                                      */
/* ------------------------------------------------------------------ */

/** VIN share médio (%) de uma concessionária — estável por dealerCode entre chamadas. */
function shareBaseConcessionaria(dealerCode: string): number {
  const random = criarRandom(hashTexto(`share-dealer-${dealerCode}`));
  return 15 + random() * 45; // 15% a 60%, faixa plausivel de unidade pra unidade
}

export function mockTrendConcessionarias(
  filtros: TrendConcessionariaFiltros = {}
): TrendConcessionariaResponse {
  const dealers =
    filtros.concessionaria && filtros.concessionaria.length > 0
      ? filtros.concessionaria
      : CONCESSIONARIAS.map((item) => item.dealerCode);
  const meses = listarMeses(
    filtros.periodoInicio ?? PERIODO_PADRAO_INICIO,
    filtros.periodoFim ?? PERIODO_PADRAO_FIM
  );

  const pontos: TrendConcessionariaResponse = [];
  for (const dealerCode of dealers) {
    const base = shareBaseConcessionaria(dealerCode);
    const random = criarRandom(hashTexto(`trend-dealer-${dealerCode}`));

    meses.forEach((mes) => {
      const ruido = (random() - 0.5) * 6;
      const valor = limitar(base + ruido, 2, 95);
      pontos.push({ data: mes, valor: arredondar(valor), categoria: dealerCode });
    });
  }

  return pontos;
}

/* ------------------------------------------------------------------ */
/* GET /api/anomalies                                                  */
/* ------------------------------------------------------------------ */

export function mockAnomalies(): AnomaliesResponse {
  const anomalias: Anomaly[] = [
    {
      tipo: "queda_dealer",
      entidade: "Ford Bahia Motors — Salvador/BA",
      severidade: 0.91,
      descricao:
        "Queda de 38% no VIN Share nos últimos 3 meses (41,2% para 25,5%). 1.184 veículos elegíveis sem retorno à rede.",
      resumo: "Queda de 38% no VIN Share nos últimos 3 meses",
      valorReferencia: 41.2,
      valorAtual: 25.5
    },
    {
      tipo: "gap_modelo",
      entidade: "KA",
      severidade: 0.84,
      descricao:
        "26,9% de VIN Share, 7,8 pontos abaixo da média da rede. Frota de 38.622 veículos com idade média de 6,4 anos.",
      resumo: "VIN Share 7,8 pontos abaixo da média da rede (frota de 38.622 veículos)",
      valorReferencia: 34.7,
      valorAtual: 26.9
    },
    {
      tipo: "pico_mainsource",
      entidade: "Ford Trioeste — Curitiba/PR",
      severidade: 0.72,
      descricao:
        "Aumento de 61% em serviços registrados fora da rede oficial em 2026. Indício de migração para oficinas independentes.",
      resumo: "Aumento de 61% em serviços registrados fora da rede oficial",
      valorReferencia: 18.5,
      valorAtual: 29.8
    },
    {
      tipo: "queda_dealer",
      entidade: "Ford Vale Sul — São José dos Campos/SP",
      severidade: 0.58,
      descricao:
        "Retenção pós-garantia caiu de 47% para 34% em 12 meses, concentrada em veículos de 4 a 7 anos.",
      resumo: "Retenção pós-garantia caiu no VIN Share em 12 meses",
      valorReferencia: 47,
      valorAtual: 34
    },
    {
      tipo: "gap_modelo",
      entidade: "ECOSPORT",
      severidade: 0.44,
      descricao:
        "Intervalo médio entre revisões subiu de 11,2 para 15,8 meses desde 2024.",
      resumo: "VIN Share abaixo da média da rede desde 2024",
      valorReferencia: 32.0,
      valorAtual: 24.0
    },
    {
      tipo: "pico_mainsource",
      entidade: "RANGER",
      severidade: 0.29,
      descricao:
        "Leve alta (9%) de serviços fora da rede em veículos acima de 8 anos, dentro do esperado para a faixa.",
      resumo: "Leve alta de serviços fora da rede em veículos acima de 8 anos",
      valorReferencia: 41.0,
      valorAtual: 44.7
    }
  ];

  return [...anomalias].sort((a, b) => b.severidade - a.severidade);
}

/* ------------------------------------------------------------------ */
/* GET /api/leads                                                      */
/* ------------------------------------------------------------------ */

const TOTAL_LEADS_MOCK = 64;

/** Modelos de justificativa; o gerador preenche com números coerentes com o score. */
function gerarMotivo(
  indiceModelo: number,
  dias: number,
  excedente: number,
  modelo: string,
  idadeAnos: number
): string {
  const motivos = [
    `${dias} dias sem serviço, ${excedente}% acima do intervalo esperado do modelo`,
    `Última revisão registrada fora da rede oficial há ${dias} dias`,
    `Garantia encerra em ${Math.max(30, 220 - dias)} dias e nenhuma revisão agendada`,
    `Histórico de 4 serviços até 2024, nenhum nos últimos ${dias} dias`,
    `${modelo} de ${idadeAnos} anos sem revisão programada desde a entrega`,
    `Intervalo médio de 11 meses rompido: ${dias} dias desde a última ordem de serviço`,
    `Queda de frequência: de 3 visitas/ano para nenhuma nos últimos ${Math.round(dias / 30)} meses`
  ];
  return motivos[indiceModelo % motivos.length];
}

function gerarLeads(): Lead[] {
  const leads: Lead[] = [];
  const modelosPonderados: string[] = [];
  for (const modelo of MODELOS) {
    const repeticoes = Math.max(1, Math.round((PESO_MODELO[modelo] ?? 0.05) * 20));
    for (let i = 0; i < repeticoes; i += 1) modelosPonderados.push(modelo);
  }

  for (let i = 0; i < TOTAL_LEADS_MOCK; i += 1) {
    const random = criarRandom(hashTexto(`lead-${i}`));
    const concessionaria = CONCESSIONARIAS[i % CONCESSIONARIAS.length];
    const modelo = modelosPonderados[Math.floor(random() * modelosPonderados.length)];

    // Distribuição intencional: ~1/3 alto, ~1/3 médio, ~1/3 baixo risco.
    const faixa = i % 3;
    const score =
      faixa === 0
        ? 0.71 + random() * 0.28
        : faixa === 1
          ? 0.31 + random() * 0.38
          : 0.04 + random() * 0.25;

    const dias = Math.round(60 + score * 480 + random() * 40);
    const excedente = Math.round(10 + score * 90);
    const idadeAnos = 1 + Math.floor(random() * 9);

    // Espelha domain/prioritization.py: valor do cliente = nº de serviços (aqui
    // simulado, 0 a 8+) normalizado em [0, 1] com teto em 8; prioridade = 70%
    // risco + 30% valor do cliente. Independente do score, para gerar casos
    // reais de divergência entre "mais risco" e "mais prioridade".
    const numeroServicos = Math.floor(random() * 10);
    const valorCliente = Math.min(numeroServicos, 8) / 8;
    const prioridade = 0.7 * score + 0.3 * valorCliente;

    leads.push({
      vin: gerarVinHash(i),
      dealerCode: concessionaria.dealerCode,
      score: arredondar(score, 2),
      motivo: gerarMotivo(i, dias, excedente, modelo, idadeAnos),
      modelo,
      diasSemServico: dias,
      prioridade: arredondar(prioridade, 2)
    });
  }

  // Mesmo desempate do backend real (issue de prioridade empatada): prioridade
  // desc, diasSemServico desc — sem isso, um empate na mock reordenaria a cada
  // geração e o desempate ficaria sem sentido de se testar na tela.
  return leads.sort((a, b) => b.prioridade - a.prioridade || b.diasSemServico - a.diasSemServico);
}

const LEADS_MOCK = gerarLeads();

/** Espelha a paginação real do backend: filtra por concessionária/score, depois pagina. */
export function mockLeads(filtros: LeadsFiltros = {}): LeadsResponse {
  const filtro = filtros.concessionaria;

  let recorte = LEADS_MOCK;
  if (filtro) {
    const concessionaria = CONCESSIONARIAS.find(
      (item) => item.dealerCode === filtro || item.nome === filtro
    );
    const dealerCode = concessionaria?.dealerCode ?? filtro;
    recorte = recorte.filter((lead) => lead.dealerCode === dealerCode);
  }
  if (filtros.scoreMinimo !== undefined) {
    recorte = recorte.filter((lead) => lead.score >= filtros.scoreMinimo!);
  }
  if (filtros.scoreMaximo !== undefined) {
    recorte = recorte.filter((lead) => lead.score < filtros.scoreMaximo!);
  }

  const tamanhoPagina = filtros.tamanhoPagina ?? 50;
  const pagina = filtros.pagina ?? 1;
  const inicio = (pagina - 1) * tamanhoPagina;

  return {
    leads: recorte.slice(inicio, inicio + tamanhoPagina),
    total: recorte.length,
    pagina,
    tamanhoPagina
  };
}

/* ------------------------------------------------------------------ */
/* GET /api/leads/distribuicao-score                                   */
/* ------------------------------------------------------------------ */

/**
 * Contagens reais observadas no dataset (175.554 leads, 10 faixas de 10 pontos) —
 * a distribuição é fortemente bimodal por como o rótulo/score é construído (ver
 * `domain.action_rules` no backend), então gerar isso a partir de uma curva
 * genérica erraria o formato que o gráfico existe pra mostrar.
 */
export function mockScoreDistribution(): ScoreDistributionResponse {
  const quantidades = [45501, 1103, 964, 387, 756, 288, 540, 440, 890, 124685];
  return quantidades.map((quantidade, indice) => ({
    faixaInicio: indice * 10,
    faixaFim: (indice + 1) * 10,
    quantidade
  }));
}

/* ------------------------------------------------------------------ */
/* GET /api/leads/{vin}/acao                                           */
/* ------------------------------------------------------------------ */

export function mockAcaoRecomendada(vin: string): AcaoRecomendada {
  const lead = LEADS_MOCK.find((item) => item.vin === vin);
  const score = lead?.score ?? 0.5;
  const modelo = lead?.modelo ?? "RANGER";
  const identificador = vin.slice(0, 8).toUpperCase();

  const acao: AcaoTipo = score > 0.7 ? "contato_ativo" : score >= 0.3 ? "oferta" : "lembrete";

  const mensagens: Record<AcaoTipo, string> = {
    contato_ativo: `Ligação prioritária: cliente do ${modelo} (VIN ${identificador}) sem passar pela rede há mais de um ano. Oferecer diagnóstico gratuito e agendamento assistido com o consultor da concessionária.`,
    oferta: `Olá! O seu ${modelo} (VIN ${identificador}) está próximo da revisão recomendada. Agende agora e garanta 15% de desconto em mão de obra na sua concessionária Ford.`,
    lembrete: `Lembrete: a próxima revisão do seu ${modelo} (VIN ${identificador}) está se aproximando. Agende pelo app Ford e mantenha a garantia e o histórico do veículo em dia.`
  };

  return { acao, mensagem: mensagens[acao] };
}

export function mockCatalogo(): Catalogo {
  return {
    modelos: [...MODELOS],
    concessionarias: CONCESSIONARIAS.map((item) => item.dealerCode),
    tiposServico: [...TIPOS_SERVICO],
    periodoDisponivel: { inicio: `${PERIODO_PADRAO_INICIO}-01`, fim: `${PERIODO_PADRAO_FIM}-30` }
  };
}

/* ------------------------------------------------------------------ */
/* GET /api/resumo-executivo                                           */
/* ------------------------------------------------------------------ */

/**
 * Reaproveita `mockAnomalies()` para as concessionárias em alerta (mesmos dados,
 * só o recorte de dealer já ordenado por severidade) — números de modelo/mês
 * calibrados pra lembrar a saída real do endpoint (ver `resumo_executivo.py`).
 */
export function mockResumoExecutivo(): ResumoExecutivo {
  const concessionariasEmAlerta = mockAnomalies()
    .filter((anomalia) => anomalia.tipo === "queda_dealer" || anomalia.tipo === "pico_mainsource")
    .sort((a, b) => b.severidade - a.severidade)
    .slice(0, 3)
    .map((anomalia) => ({
      dealerCode: anomalia.entidade,
      tipo: anomalia.tipo,
      severidade: anomalia.severidade,
      resumo: anomalia.resumo
    }));

  return {
    concessionariasEmAlerta,
    modelosMaiorRisco: [
      { modelo: "KA", percentualAltoRisco: 94.6, totalVeiculos: 50373 },
      { modelo: "ECOSPORT", percentualAltoRisco: 89.7, totalVeiculos: 16010 },
      { modelo: "TRANSIT", percentualAltoRisco: 81.6, totalVeiculos: 4120 }
    ],
    mesesMaiorChurn: [
      { competencia: "2024-06", vinShareRede: 3.9 },
      { competencia: "2024-05", vinShareRede: 4.0 },
      { competencia: "2024-09", vinShareRede: 4.2 }
    ]
  };
}
