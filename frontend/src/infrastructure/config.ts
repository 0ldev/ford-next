/**
 * Configuração central da camada de infraestrutura.
 */

/**
 * Alterna entre a fonte de dados mockada e a API real.
 *
 * Enquanto os endpoints do backend não estiverem no ar, o dashboard roda
 * inteiro sobre `mockData.ts`, que respeita os mesmos tipos de `domain/types`.
 *
 * TODO: trocar para false quando a API do Bruno estiver no ar.
 */
export const USE_MOCK = true;

/**
 * Prefixo dos endpoints. Em desenvolvimento o Vite faz proxy de `/api`
 * para http://localhost:8000 (ver vite.config.ts), então o caminho
 * relativo funciona sem configuração extra.
 */
export const API_BASE_URL = "/api";

/** Latência simulada (ms) da fonte mockada, para exercitar os estados de loading. */
export const MOCK_LATENCY_MS = 250;
