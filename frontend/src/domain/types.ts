/**
 * Contratos de dados do VIN Share Intelligence Hub.
 *
 * Estes tipos espelham o schema acordado com o backend (FastAPI) e são a
 * única fonte de verdade do frontend: tanto a API real quanto a fonte
 * mockada devem satisfazê-los. Qualquer divergência aparece como erro de
 * compilação, não como bug em runtime.
 */

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
}

export type LeadsResponse = Lead[];

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

/** Filtros da tabela de leads. */
export interface LeadsFiltros {
  concessionaria?: string;
}
