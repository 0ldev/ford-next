export interface VinShareResponse {
  vinShareEstimado: number;
  totalVeiculosElegiveis: number;
  totalComServico: number;
  filtrosAplicados: Record<string, string | null>;
}

export interface TrendPoint {
  data: string;
  valor: number;
  categoria: string;
}

export type TrendResponse = TrendPoint[];

export type TrendConcessionariaResponse = TrendPoint[];

export type AnomalyTipo = "queda_dealer" | "gap_modelo" | "pico_mainsource";

export interface Anomaly {
  tipo: AnomalyTipo;
  entidade: string;
  severidade: number;
  descricao: string;
  resumo: string;
  valorReferencia: number;
  valorAtual: number;
}

export type AnomaliesResponse = Anomaly[];

export interface Lead {
  vin: string;
  dealerCode: string;
  score: number;
  motivo: string;
  modelo: string;
  diasSemServico: number;
  prioridade: number;
}

export interface LeadsResponse {
  leads: Lead[];
  total: number;
  pagina: number;
  tamanhoPagina: number;
}

export interface FaixaScore {
  faixaInicio: number;
  faixaFim: number;
  quantidade: number;
}

export type ScoreDistributionResponse = FaixaScore[];

export type AcaoTipo = "lembrete" | "oferta" | "contato_ativo";

export interface AcaoRecomendada {
  acao: AcaoTipo;
  mensagem: string;
}

export interface PeriodoDisponivel {
  inicio: string;
  fim: string;
}

export interface Catalogo {
  modelos: string[];
  concessionarias: string[];
  tiposServico: string[];
  periodoDisponivel: PeriodoDisponivel | null;
}

export interface VinShareFiltros {
  concessionaria?: string;
  modelo?: string;
  faixaIdade?: string;
  tipoServico?: string;
  periodoInicio?: string;
  periodoFim?: string;
}

export interface TrendFiltros {
  modelo?: string[];
  periodoInicio?: string;
  periodoFim?: string;
}

export interface TrendConcessionariaFiltros {
  concessionaria?: string[];
  periodoInicio?: string;
  periodoFim?: string;
  minVeiculos?: number;
}

export interface LeadsFiltros {
  concessionaria?: string;
  scoreMinimo?: number;
  scoreMaximo?: number;
  pagina?: number;
  tamanhoPagina?: number;
}
