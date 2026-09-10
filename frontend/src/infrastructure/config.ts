/**
 * Configuração central da camada de infraestrutura.
 */

/**
 * Alterna entre a fonte de dados mockada e a API real.
 *
 * A API do Bruno está no ar e integrada (issue #8) — `mockData.ts` continua
 * existindo para desenvolvimento offline/demonstração sem backend, mas o
 * dashboard real usa a API.
 */
export const USE_MOCK = false;

/**
 * Prefixo dos endpoints. Em desenvolvimento o Vite faz proxy de `/api`
 * para http://localhost:8000 (ver vite.config.ts), então o caminho
 * relativo funciona sem configuração extra.
 */
export const API_BASE_URL = "/api";

/** Latência simulada (ms) da fonte mockada, para exercitar os estados de loading. */
export const MOCK_LATENCY_MS = 250;
