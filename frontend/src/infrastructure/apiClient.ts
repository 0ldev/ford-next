import { API_BASE_URL } from "./config";

/** Valores aceitos em query string. Arrays viram chaves repetidas. */
export type QueryParamValue = string | number | boolean | string[] | undefined | null;
export type QueryParams = Record<string, QueryParamValue>;

/** Origem da falha, para a UI decidir a mensagem exibida. */
export type ApiErrorKind = "http" | "network" | "parse";

/**
 * Erro tipado emitido por `apiGet`. Todo caminho de falha — HTTP não-2xx,
 * rede indisponível ou JSON inválido — termina aqui, de forma que a camada
 * de aplicação nunca precise lidar com exceções desconhecidas do fetch.
 */
export class ApiError extends Error {
  /** Status HTTP; 0 quando a requisição sequer chegou ao servidor. */
  readonly status: number;
  readonly kind: ApiErrorKind;
  /** URL que falhou, útil para diagnóstico. */
  readonly url: string;
  /** Corpo bruto da resposta de erro, quando houver. */
  readonly body?: string;

  constructor(params: {
    message: string;
    status: number;
    kind: ApiErrorKind;
    url: string;
    body?: string;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.status = params.status;
    this.kind = params.kind;
    this.url = params.url;
    this.body = params.body;
  }
}

/** Garante que qualquer erro capturado vire um `ApiError` legível pela UI. */
export function toApiError(erro: unknown, url = ""): ApiError {
  if (erro instanceof ApiError) return erro;
  const message = erro instanceof Error ? erro.message : String(erro);
  return new ApiError({
    message: `Falha de rede ao acessar ${url || "a API"}: ${message}`,
    status: 0,
    kind: "network",
    url
  });
}

/**
 * Monta a query string ignorando parâmetros ausentes (`undefined`, `null`,
 * string vazia) e arrays vazios. Arrays viram chaves repetidas
 * (`modelo=RANGER&modelo=KA`), convenção a confirmar com o backend.
 */
export function buildQueryString(params?: QueryParams): string {
  if (!params) return "";

  const search = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params)) {
    if (valor === undefined || valor === null) continue;

    if (Array.isArray(valor)) {
      for (const item of valor) {
        if (item !== "") search.append(chave, item);
      }
      continue;
    }

    const texto = String(valor);
    if (texto !== "") search.append(chave, texto);
  }

  const query = search.toString();
  return query ? `?${query}` : "";
}

/** Junta base e path evitando barra dupla ou barra faltando. */
function buildUrl(path: string, params?: QueryParams): string {
  const base = API_BASE_URL.replace(/\/+$/, "");
  const rota = path.startsWith("/") ? path : `/${path}`;
  return `${base}${rota}${buildQueryString(params)}`;
}

/** Extrai a mensagem de erro do corpo da resposta, se ele for JSON com `detail`/`message`. */
function extrairMensagem(body: string, status: number, statusText: string): string {
  if (body) {
    try {
      const json: unknown = JSON.parse(body);
      if (json && typeof json === "object") {
        const registro = json as Record<string, unknown>;
        const detalhe = registro.detail ?? registro.message ?? registro.erro;
        if (typeof detalhe === "string" && detalhe !== "") return detalhe;
      }
    } catch {
      // corpo não-JSON: cai no texto padrão abaixo
    }
  }
  return `Erro ${status}${statusText ? ` (${statusText})` : ""} ao consultar a API.`;
}

/**
 * GET tipado. Sempre rejeita com `ApiError` — nunca com um erro cru do fetch.
 */
export async function apiGet<T>(path: string, params?: QueryParams): Promise<T> {
  const url = buildUrl(path, params);

  let resposta: Response;
  try {
    resposta = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" }
    });
  } catch (erro) {
    throw toApiError(erro, url);
  }

  if (!resposta.ok) {
    let body = "";
    try {
      body = await resposta.text();
    } catch {
      // corpo ilegível não deve mascarar o status HTTP
    }
    throw new ApiError({
      message: extrairMensagem(body, resposta.status, resposta.statusText),
      status: resposta.status,
      kind: "http",
      url,
      body: body || undefined
    });
  }

  try {
    return (await resposta.json()) as T;
  } catch (erro) {
    throw new ApiError({
      message: `Resposta da API não é um JSON válido: ${
        erro instanceof Error ? erro.message : String(erro)
      }`,
      status: resposta.status,
      kind: "parse",
      url
    });
  }
}
