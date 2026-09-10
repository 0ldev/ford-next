import { describe, expect, it } from "vitest";
import { LIMIAR_ALTO, LIMIAR_MEDIO, nivelDeRisco } from "./severidade";

describe("nivelDeRisco", () => {
  it("classifica pelos limiares compartilhados", () => {
    expect(nivelDeRisco(0.91)).toBe("alto");
    expect(nivelDeRisco(0.5)).toBe("medio");
    expect(nivelDeRisco(0.12)).toBe("baixo");
  });

  it("inclui o próprio limiar na faixa de cima", () => {
    expect(nivelDeRisco(LIMIAR_ALTO)).toBe("alto");
    expect(nivelDeRisco(LIMIAR_MEDIO)).toBe("medio");
  });

  it("trata os extremos", () => {
    expect(nivelDeRisco(0)).toBe("baixo");
    expect(nivelDeRisco(1)).toBe("alto");
  });

  it("usa o mesmo corte que a tabela de leads usava (0,3)", () => {
    // Regressão da auditoria: o painel de anomalias cortava "médio" em 0,4,
    // então 0,35 aparecia baixo nas anomalias e médio nos leads, com as duas
    // telas usando a mesma escala de cores.
    expect(LIMIAR_MEDIO).toBe(0.3);
    expect(nivelDeRisco(0.35)).toBe("medio");
    expect(nivelDeRisco(0.29)).toBe("baixo");
  });
});
