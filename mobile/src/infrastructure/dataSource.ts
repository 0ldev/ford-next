import type {
  AcaoRecomendada,
  AnomaliesResponse,
  Catalogo,
  LeadsFiltros,
  LeadsResponse,
  ScoreDistributionResponse,
  TrendConcessionariaFiltros,
  TrendConcessionariaResponse,
  TrendFiltros,
  TrendResponse,
  VinShareFiltros,
  VinShareResponse
} from "../domain/types";
import { LATENCIA_SIMULADA_MS } from "./config";
import {
  mockAcaoRecomendada,
  mockAnomalies,
  mockCatalogo,
  mockLeads,
  mockScoreDistribution,
  mockTrend,
  mockTrendConcessionarias,
  mockVinShare
} from "./mockData";

function comLatencia<T>(valor: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(valor), LATENCIA_SIMULADA_MS);
  });
}

export function buscarVinShare(filtros: VinShareFiltros = {}): Promise<VinShareResponse> {
  return comLatencia(mockVinShare(filtros));
}

export function buscarTrend(filtros: TrendFiltros = {}): Promise<TrendResponse> {
  return comLatencia(mockTrend(filtros));
}

export function buscarAnomalies(): Promise<AnomaliesResponse> {
  return comLatencia(mockAnomalies());
}

export function buscarLeads(filtros: LeadsFiltros = {}): Promise<LeadsResponse> {
  return comLatencia(mockLeads(filtros));
}

export function buscarAcaoRecomendada(vin: string): Promise<AcaoRecomendada> {
  return comLatencia(mockAcaoRecomendada(vin));
}

export function buscarCatalogo(): Promise<Catalogo> {
  return comLatencia(mockCatalogo());
}

export function buscarTrendConcessionarias(
  filtros: TrendConcessionariaFiltros = {}
): Promise<TrendConcessionariaResponse> {
  return comLatencia(mockTrendConcessionarias(filtros));
}

export function buscarDistribuicaoScore(): Promise<ScoreDistributionResponse> {
  return comLatencia(mockScoreDistribution());
}
