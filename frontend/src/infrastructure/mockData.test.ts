import { describe, expect, it } from "vitest";
import { mockLeads, mockVinShare } from "./mockData";

const INTERVALOS: [string, string][] = [
  ["2025-01-01", "2025-12-31"],
  ["2025-01-01", "2026-06-30"],
  ["2026-01-01", "2026-06-30"],
  ["2026-02-01", "2026-02-28"],
  ["2024-03-01", "2024-08-31"]
];

describe("mockVinShare — variação por período", () => {
  const semPeriodo = mockVinShare({}).vinShareEstimado;

  it("desloca o indicador de 3 a 5 pontos percentuais", () => {
    for (const [periodoInicio, periodoFim] of INTERVALOS) {
      const { vinShareEstimado } = mockVinShare({ periodoInicio, periodoFim });
      const delta = Math.abs(vinShareEstimado - semPeriodo);

      expect(delta).toBeGreaterThanOrEqual(2.9);
      expect(delta).toBeLessThanOrEqual(5.1);
    }
  });

  it("dá valores distintos para intervalos distintos", () => {
    // Regressão: com a semente sem avalanche, datas diferentes caíam no
    // mesmo ajuste e o KPI não mudava ao trocar o período.
    const valores = INTERVALOS.map(
      ([periodoInicio, periodoFim]) => mockVinShare({ periodoInicio, periodoFim }).vinShareEstimado
    );

    expect(new Set(valores).size).toBe(valores.length);
  });

  it("é estável para o mesmo intervalo", () => {
    const primeiro = mockVinShare({ periodoInicio: "2025-01-01", periodoFim: "2025-12-31" });
    const segundo = mockVinShare({ periodoInicio: "2025-01-01", periodoFim: "2025-12-31" });

    expect(primeiro).toEqual(segundo);
  });

  it("mantém totalComServico coerente com o percentual", () => {
    const { vinShareEstimado, totalComServico, totalVeiculosElegiveis } = mockVinShare({
      periodoInicio: "2025-01-01",
      periodoFim: "2025-12-31"
    });

    expect(totalComServico).toBe(
      Math.round((totalVeiculosElegiveis * vinShareEstimado) / 100)
    );
  });
});

describe("mockLeads", () => {
  it("cobre as três faixas de risco com VINs únicos", () => {
    const leads = mockLeads();

    expect(leads.filter((lead) => lead.score > 0.7).length).toBeGreaterThan(0);
    expect(leads.filter((lead) => lead.score >= 0.3 && lead.score <= 0.7).length).toBeGreaterThan(0);
    expect(leads.filter((lead) => lead.score < 0.3).length).toBeGreaterThan(0);
    expect(new Set(leads.map((lead) => lead.vin)).size).toBe(leads.length);
  });
});
