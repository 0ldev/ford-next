import { describe, expect, it } from "vitest";
import { descreverFiltros, formatarDataBR } from "./ResumoFiltros";

describe("descreverFiltros", () => {
  it("descreve a rede inteira quando não há filtro", () => {
    expect(descreverFiltros({})).toBe("todos os veículos elegíveis da rede, em todo o período");
  });

  it("usa o nome da concessionária, não o código", () => {
    expect(descreverFiltros({ concessionaria: "BR0142" })).toContain("Ford Sorana");
  });

  it("liga o último trecho com 'e'", () => {
    expect(descreverFiltros({ modelo: "KA", faixaIdade: "2-4" })).toBe(
      "modelo KA e veículos de 2-4 anos"
    );
  });

  it("descreve período aberto de um lado só", () => {
    expect(descreverFiltros({ periodoInicio: "2025-01-01" })).toBe("a partir de 01/01/2025");
    expect(descreverFiltros({ periodoFim: "2025-12-31" })).toBe("até 31/12/2025");
  });

  it("acumula os seis filtros numa frase", () => {
    const frase = descreverFiltros({
      concessionaria: "BR0731",
      modelo: "RANGER",
      faixaIdade: "4+",
      tipoServico: "Garantia",
      periodoInicio: "2025-01-01",
      periodoFim: "2025-12-31"
    });

    expect(frase).toBe(
      "concessionária Ford Bahia Motors — Salvador/BA, modelo RANGER, veículos de 4+ anos, " +
        "serviços de garantia e de 01/01/2025 a 31/12/2025"
    );
  });
});

describe("formatarDataBR", () => {
  it("converte ISO para o formato brasileiro", () => {
    expect(formatarDataBR("2026-02-09")).toBe("09/02/2026");
  });

  it("não desloca o dia por fuso horário", () => {
    // new Date("2025-01-01") seria lido como UTC e mostraria 31/12/2024 no Brasil.
    expect(formatarDataBR("2025-01-01")).toBe("01/01/2025");
  });
});
