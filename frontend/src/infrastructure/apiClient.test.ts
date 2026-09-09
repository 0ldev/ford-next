import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiGet, buildQueryString, toApiError } from "./apiClient";

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

afterEach(() => {
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
