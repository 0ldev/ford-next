/**
 * Fonte de dados única do dashboard.
 *
 * É o único ponto que decide entre mock e API real (flag `USE_MOCK` em
 * `config.ts`). Os hooks da camada de aplicação chamam sempre estas funções,
 * então trocar a flag quando o backend estiver no ar não exige reescrever
 * nenhum hook nem nenhum componente.
 */

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
import { apiGet } from "./apiClient";
import { MOCK_LATENCY_MS, USE_MOCK } from "./config";
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

/** Simula a latência da rede para que os estados de loading sejam reais na UI. */
function comLatencia<T>(valor: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(valor), MOCK_LATENCY_MS);
  });
}

export function buscarVinShare(filtros: VinShareFiltros = {}): Promise<VinShareResponse> {
  if (USE_MOCK) return comLatencia(mockVinShare(filtros));
  return apiGet<VinShareResponse>("/vin-share", { ...filtros });
}

export function buscarTrend(filtros: TrendFiltros = {}): Promise<TrendResponse> {
  if (USE_MOCK) return comLatencia(mockTrend(filtros));
  return apiGet<TrendResponse>("/trend", { ...filtros });
}

export function buscarAnomalies(): Promise<AnomaliesResponse> {
  if (USE_MOCK) return comLatencia(mockAnomalies());
  return apiGet<AnomaliesResponse>("/anomalies");
}

export function buscarLeads(filtros: LeadsFiltros = {}): Promise<LeadsResponse> {
  if (USE_MOCK) return comLatencia(mockLeads(filtros));
  return apiGet<LeadsResponse>("/leads", { ...filtros });
}

export function buscarAcaoRecomendada(vin: string): Promise<AcaoRecomendada> {
  if (USE_MOCK) return comLatencia(mockAcaoRecomendada(vin));
  return apiGet<AcaoRecomendada>(`/leads/${encodeURIComponent(vin)}/acao`);
}

export function buscarCatalogo(): Promise<Catalogo> {
  if (USE_MOCK) return comLatencia(mockCatalogo());
  return apiGet<Catalogo>("/catalogo");
}

export function buscarTrendConcessionarias(
  filtros: TrendConcessionariaFiltros = {}
): Promise<TrendConcessionariaResponse> {
  if (USE_MOCK) return comLatencia(mockTrendConcessionarias(filtros));
  return apiGet<TrendConcessionariaResponse>("/trend/concessionarias", { ...filtros });
}

export function buscarDistribuicaoScore(): Promise<ScoreDistributionResponse> {
  if (USE_MOCK) return comLatencia(mockScoreDistribution());
  return apiGet<ScoreDistributionResponse>("/leads/distribuicao-score");
}
