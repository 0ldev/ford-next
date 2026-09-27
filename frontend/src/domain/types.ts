/**
 * Contratos de dados do VIN Share Intelligence Hub.
 *
 * Estes tipos espelham o schema acordado com o backend (FastAPI) e são a
 * única fonte de verdade do frontend: tanto a API real quanto a fonte
 * mockada devem satisfazê-los. Qualquer divergência aparece como erro de
 * compilação, não como bug em runtime.
 */

/* ------------------------------------------------------------------ */
/* POST /api/auth/login                                                */
/* ------------------------------------------------------------------ */

export type Perfil = "gestor" | "concessionaria";

export interface CredenciaisLogin {
  usuario: string;
  senha: string;
}

/** Resposta de `POST /api/auth/login` — o que persiste em `infrastructure/session.ts`. */
export interface Sessao {
  token: string;
  perfil: Perfil;
  /** `null` para perfil `gestor` (acesso à rede toda). */
  dealerCode: string | null;
  /** ISO 8601 — quando o token expira. */
  expiraEm: string;
}

/* ------------------------------------------------------------------ */
/* GET /api/vin-share                                                  */
/* ------------------------------------------------------------------ */

export interface VinShareResponse {
  /** Percentual de 0 a 100. */
  vinShareEstimado: number;
  totalVeiculosElegiveis: number;
  totalComServico: number;
  /** Eco dos filtros considerados pelo backend; `null` = filtro não aplicado. */
  filtrosAplicados: Record<string, string | null>;
}

/* ------------------------------------------------------------------ */
/* GET /api/trend                                                      */
/* ------------------------------------------------------------------ */

export interface TrendPoint {
  /** Competência no formato "YYYY-MM". */
  data: string;
  /** VIN share (%) da categoria naquele mês. */
  valor: number;
  /** Nome do modelo (série do gráfico). */
  categoria: string;
}

export type TrendResponse = TrendPoint[];

/* ------------------------------------------------------------------ */
/* GET /api/trend/concessionarias                                      */
/* ------------------------------------------------------------------ */

/** Mesmo schema de `TrendPoint`, só que `categoria` é o dealerCode. */
export type TrendConcessionariaResponse = TrendPoint[];

/* ------------------------------------------------------------------ */
/* GET /api/anomalies                                                  */
/* ------------------------------------------------------------------ */

export type AnomalyTipo = "queda_dealer" | "gap_modelo" | "pico_mainsource";

export interface Anomaly {
  tipo: AnomalyTipo;
  /** Nome da concessionária ou do modelo afetado. */
  entidade: string;
  /** 0 a 1 — usado para destaque visual (cor/ordem). */
  severidade: number;
  /** Texto pronto para exibição, sem necessidade de formatação extra. */
  descricao: string;
  /** Mesma frase de `descricao`, sem o parêntese de valores — para o card visual. */
  resumo: string;
  /**
   * `valorReferencia` -> `valorAtual`, ambos em % (mesma escala nos 3 tipos).
   * Para `gap_modelo`, `valorReferencia` é a média da rede (não um "antes" temporal).
   */
  valorReferencia: number;
  valorAtual: number;
}

export type AnomaliesResponse = Anomaly[];

/* ------------------------------------------------------------------ */
/* GET /api/leads                                                      */
/* ------------------------------------------------------------------ */

export interface Lead {
  /** VIN anonimizado (hash) — identificador do veículo. */
  vin: string;
  dealerCode: string;
  /** Risco de evasão, 0 a 1. */
  score: number;
  /** Justificativa legível do score, gerada pelo modelo. */
  motivo: string;
  modelo: string;
  /** Dias desde o último serviço — critério de desempate da prioridade. */
  diasSemServico: number;
  /**
   * Prioridade final de contato, 0 a 1: cruza `score` (risco) com o valor do
   * cliente (histórico de serviços) — ver `domain/prioritization.py` no backend.
   * É o critério de ordenação da fila, não `score` sozinho.
   */
  prioridade: number;
}

/**
 * Página do resultado de `/api/leads`. `total` é a contagem do recorte inteiro
 * (após concessionaria/scoreMinimo, antes de paginar) — é o que permite a tela
 * mostrar "50 de 3214" e montar os botões de anterior/próxima.
 */
export interface LeadsResponse {
  leads: Lead[];
  total: number;
  pagina: number;
  tamanhoPagina: number;
}

/* ------------------------------------------------------------------ */
/* GET /api/leads/distribuicao-score                                   */
/* ------------------------------------------------------------------ */

export interface FaixaScore {
  /** % (0-100), limite inferior da faixa. */
  faixaInicio: number;
  /** % (0-100), limite superior da faixa (inclusive). */
  faixaFim: number;
  quantidade: number;
}

export type ScoreDistributionResponse = FaixaScore[];

/* ------------------------------------------------------------------ */
/* GET /api/leads/{vin}/acao                                           */
/* ------------------------------------------------------------------ */

export type AcaoTipo = "lembrete" | "oferta" | "contato_ativo";

export interface AcaoRecomendada {
  acao: AcaoTipo;
  /** Mensagem já personalizada com os dados do veículo. */
  mensagem: string;
}

/* ------------------------------------------------------------------ */
/* GET /api/resumo-executivo                                           */
/* ------------------------------------------------------------------ */

export interface ConcessionariaEmAlerta {
  dealerCode: string;
  tipo: AnomalyTipo;
  /** 0 a 1 — mesma escala de `Anomaly.severidade`. */
  severidade: number;
  resumo: string;
}

export interface ModeloMaiorRisco {
  modelo: string;
  /** % da frota do modelo com score de risco alto (>= 70%). */
  percentualAltoRisco: number;
  totalVeiculos: number;
}

export interface MesMaiorChurn {
  /** Competência no formato "YYYY-MM". */
  competencia: string;
  /** VIN Share da rede inteira naquele mês (%). */
  vinShareRede: number;
}

/**
 * As três listas do "bateu o olho": onde agir primeiro, sem precisar navegar o
 * resto do dashboard. Cada lista já vem em ordem de prioridade (pior primeiro).
 */
export interface ResumoExecutivo {
  concessionariasEmAlerta: ConcessionariaEmAlerta[];
  modelosMaiorRisco: ModeloMaiorRisco[];
  mesesMaiorChurn: MesMaiorChurn[];
}

/* ------------------------------------------------------------------ */
/* GET /api/catalogo                                                   */
/* ------------------------------------------------------------------ */

/** Início/fim (ISO "YYYY-MM-DD") do intervalo de datas com dado real no histórico. */
export interface PeriodoDisponivel {
  inicio: string;
  fim: string;
}

/** Valores reais distintos do dataset — opções verdadeiras dos filtros do dashboard. */
export interface Catalogo {
  modelos: string[];
  concessionarias: string[];
  tiposServico: string[];
  /** `null` só no caso degenerado de o histórico não ter nenhuma data de serviço válida. */
  periodoDisponivel: PeriodoDisponivel | null;
}

/* ------------------------------------------------------------------ */
/* Filtros                                                             */
/* ------------------------------------------------------------------ */

/**
 * Filtros da barra de filtros cruzados. Todos opcionais: ausente ou vazio
 * significa "sem restrição" e é omitido da query string.
 */
export interface VinShareFiltros {
  concessionaria?: string;
  modelo?: string;
  /** Faixa de idade do veículo em anos: "0-1", "1-2", "2-4" ou "4+". */
  faixaIdade?: string;
  tipoServico?: string;
  /** Início do período, data ISO "YYYY-MM-DD". */
  periodoInicio?: string;
  /** Fim do período, data ISO "YYYY-MM-DD". */
  periodoFim?: string;
}

/** Filtros do gráfico de tendência — aceita múltiplos modelos (uma série cada). */
export interface TrendFiltros {
  modelo?: string[];
  periodoInicio?: string;
  periodoFim?: string;
}

/** Filtros do ranking de VIN Share por concessionária. */
export interface TrendConcessionariaFiltros {
  concessionaria?: string[];
  periodoInicio?: string;
  periodoFim?: string;
  /** Piso de VINs elegíveis; ignorado se `concessionaria` for informado. */
  minVeiculos?: number;
}

/** Filtros da tabela de leads. */
export interface LeadsFiltros {
  concessionaria?: string;
  /** Piso de score (0-1); ausente = sem piso, traz a fila inteira paginada. */
  scoreMinimo?: number;
  /** Teto exclusivo de score (0-1): só leads com score < esse valor. */
  scoreMaximo?: number;
  /** 1-based; ausente = primeira página. */
  pagina?: number;
  /** Ausente = padrão do backend (50). */
  tamanhoPagina?: number;
}
