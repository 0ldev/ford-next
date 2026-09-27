import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Sessao } from "../domain/types";
import { limparSessao, obterSessao, salvarSessao, sessaoValida } from "./session";

function sessaoFutura(minutos = 60): Sessao {
  return {
    token: "token-de-teste",
    perfil: "gestor",
    dealerCode: null,
    expiraEm: new Date(Date.now() + minutos * 60_000).toISOString()
  };
}

/**
 * O ambiente de teste roda em Node puro (sem jsdom), que não tem
 * `localStorage` global — o mesmo motivo pelo qual `session.ts` protege cada
 * chamada com try/catch (funciona igual num navegador com storage bloqueado).
 * Um stub em memória é suficiente pra exercitar o roundtrip real.
 */
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

beforeEach(() => {
  vi.stubGlobal("localStorage", criarLocalStorageStub());
});

afterEach(() => {
  limparSessao();
  vi.unstubAllGlobals();
});

describe("salvarSessao / obterSessao / limparSessao", () => {
  it("faz roundtrip: o que é salvo é o que volta", () => {
    const sessao = sessaoFutura();
    salvarSessao(sessao);

    expect(obterSessao()).toEqual(sessao);
  });

  it("devolve null quando nunca houve sessão salva", () => {
    expect(obterSessao()).toBeNull();
  });

  it("limparSessao remove a sessão salva", () => {
    salvarSessao(sessaoFutura());
    limparSessao();

    expect(obterSessao()).toBeNull();
  });
});

describe("sessaoValida", () => {
  it("é true para uma sessão com expiração no futuro", () => {
    expect(sessaoValida(sessaoFutura(60))).toBe(true);
  });

  it("é false para uma sessão já expirada", () => {
    expect(sessaoValida(sessaoFutura(-1))).toBe(false);
  });

  it("é false para null/undefined", () => {
    expect(sessaoValida(null)).toBe(false);
    expect(sessaoValida(undefined)).toBe(false);
  });
});
