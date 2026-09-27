import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Sessao } from "../domain/types";
import { ApiError, apiGet, apiPost, buildQueryString, toApiError } from "./apiClient";
import { limparSessao, salvarSessao } from "./session";

/** Ambiente de teste é Node puro (sem jsdom): stub em memória pro `localStorage` que `session.ts` usa. */
function criarLocalStorageStub(): Storage {
  const dados = new Map<string, string>();
  return {
    getItem: (chave: string) => dados.get(chave) ?? null,
    setItem: (chave: string, valor: string) => {
      dados.set(chave, valor);
    },
    removeItem: (chave: string) => {
      dados.delete(chave);
    },
    clear: () => dados.clear(),
    key: (indice: number) => [...dados.keys()][indice] ?? null,
    get length() {
      return dados.size;
    }
  } as Storage;
}

/** Substitui o fetch global por um duplo controlado pelo teste. */
function mockarFetch(implementacao: () => Promise<Response>): void {
  vi.stubGlobal("fetch", vi.fn(implementacao));
}

function respostaJson(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

/** URL efetivamente chamada na primeira invocação do fetch mockado. */
function urlChamada(): string {
  const chamada = vi.mocked(fetch).mock.calls[0];
  return String(chamada[0]);
}

/** `init.headers` efetivamente passado na primeira invocação do fetch mockado. */
function headersChamados(): Headers {
  const chamada = vi.mocked(fetch).mock.calls[0];
  return new Headers(chamada[1]?.headers);
}

function sessaoDeTeste(): Sessao {
  return {
    token: "token-abc123",
    perfil: "gestor",
    dealerCode: null,
    expiraEm: new Date(Date.now() + 60_000).toISOString()
  };
}

beforeEach(() => {
  vi.stubGlobal("localStorage", criarLocalStorageStub());
});

afterEach(() => {
  limparSessao();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("buildQueryString", () => {
  it("omite parâmetros ausentes ou vazios", () => {
    const query = buildQueryString({
      modelo: "RANGER",
      concessionaria: undefined,
      faixaIdade: null,
      tipoServico: ""
    });

    expect(query).toBe("?modelo=RANGER");
  });

  it("devolve string vazia quando não há nenhum parâmetro útil", () => {
    expect(buildQueryString()).toBe("");
    expect(buildQueryString({ modelo: undefined })).toBe("");
  });

  it("serializa arrays como chaves repetidas", () => {
    expect(buildQueryString({ modelo: ["RANGER", "KA"] })).toBe("?modelo=RANGER&modelo=KA");
  });
});

describe("apiGet", () => {
  it("devolve o JSON tipado em uma resposta 2xx", async () => {
    const payload = {
      vinShareEstimado: 34.7,
      totalVeiculosElegiveis: 175554,
      totalComServico: 60917,
      filtrosAplicados: { modelo: null }
    };
    mockarFetch(async () => respostaJson(payload));

    const resultado = await apiGet<typeof payload>("/vin-share");

    expect(resultado).toEqual(payload);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("monta a URL com base, path e query string", async () => {
    mockarFetch(async () => respostaJson([]));

    await apiGet("/leads", { concessionaria: "BR0142", modelo: undefined });

    expect(urlChamada()).toBe("/api/leads?concessionaria=BR0142");
  });

  it("lança ApiError tratável quando a resposta não é 2xx", async () => {
    mockarFetch(async () => respostaJson({ detail: "Concessionária não encontrada" }, 404));

    const erro = await apiGet("/vin-share").catch((e: unknown) => e);

    expect(erro).toBeInstanceOf(ApiError);
    const apiError = erro as ApiError;
    expect(apiError.kind).toBe("http");
    expect(apiError.status).toBe(404);
    expect(apiError.message).toBe("Concessionária não encontrada");
  });

  it("usa mensagem padrão quando o corpo do erro não traz detalhe", async () => {
    mockarFetch(async () => new Response("<html>500</html>", { status: 500 }));

    const erro = (await apiGet("/trend").catch((e: unknown) => e)) as ApiError;

    expect(erro).toBeInstanceOf(ApiError);
    expect(erro.status).toBe(500);
    expect(erro.message).toContain("Erro 500");
  });

  it("converte falha de rede em ApiError com status 0", async () => {
    mockarFetch(async () => {
      throw new TypeError("Failed to fetch");
    });

    const erro = (await apiGet("/anomalies").catch((e: unknown) => e)) as ApiError;

    expect(erro).toBeInstanceOf(ApiError);
    expect(erro.kind).toBe("network");
    expect(erro.status).toBe(0);
    expect(erro.message).toContain("Failed to fetch");
  });

  it("sinaliza JSON inválido como erro de parse", async () => {
    mockarFetch(async () => new Response("isto não é json", { status: 200 }));

    const erro = (await apiGet("/leads").catch((e: unknown) => e)) as ApiError;

    expect(erro).toBeInstanceOf(ApiError);
    expect(erro.kind).toBe("parse");
  });
});

describe("apiGet — Authorization", () => {
  it("não envia Authorization sem sessão ativa", async () => {
    mockarFetch(async () => respostaJson({}));
    await apiGet("/catalogo");

    expect(headersChamados().has("Authorization")).toBe(false);
  });

  it("envia Authorization: Bearer <token> com sessão ativa", async () => {
    salvarSessao(sessaoDeTeste());
    mockarFetch(async () => respostaJson({}));
    await apiGet("/catalogo");

    expect(headersChamados().get("Authorization")).toBe("Bearer token-abc123");
  });
});

describe("apiPost", () => {
  it("envia o corpo serializado como JSON e devolve o JSON tipado da resposta", async () => {
    mockarFetch(async () => respostaJson({ token: "novo-token" }));

    const resultado = await apiPost<{ token: string }>("/auth/login", { usuario: "gestor", senha: "gestor123" });

    expect(resultado).toEqual({ token: "novo-token" });
    const chamada = vi.mocked(fetch).mock.calls[0];
    expect(chamada[1]?.method).toBe("POST");
    expect(chamada[1]?.body).toBe(JSON.stringify({ usuario: "gestor", senha: "gestor123" }));
    expect(headersChamados().get("Content-Type")).toBe("application/json");
  });

  it("também anexa Authorization quando há sessão ativa", async () => {
    salvarSessao(sessaoDeTeste());
    mockarFetch(async () => respostaJson({}));

    await apiPost("/leads/v1/contatos", { acao: "oferta" });

    expect(headersChamados().get("Authorization")).toBe("Bearer token-abc123");
  });

  it("lança ApiError tratável quando a resposta não é 2xx", async () => {
    mockarFetch(async () => respostaJson({ detail: "Usuário ou senha inválidos." }, 401));

    const erro = (await apiPost("/auth/login", { usuario: "x", senha: "y" }).catch((e: unknown) => e)) as ApiError;

    expect(erro).toBeInstanceOf(ApiError);
    expect(erro.status).toBe(401);
    expect(erro.message).toBe("Usuário ou senha inválidos.");
  });
});

describe("toApiError", () => {
  it("preserva um ApiError já tipado", () => {
    const original = new ApiError({
      message: "erro original",
      status: 503,
      kind: "http",
      url: "/api/leads"
    });

    expect(toApiError(original)).toBe(original);
  });

  it("embrulha erros desconhecidos como falha de rede", () => {
    const erro = toApiError("queda de conexão", "/api/trend");

    expect(erro).toBeInstanceOf(ApiError);
    expect(erro.kind).toBe("network");
    expect(erro.status).toBe(0);
  });
});
