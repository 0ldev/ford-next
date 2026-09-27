export const cores = {
  azul900: "#000733",
  azul800: "#00095b",
  azul600: "#1d3f9e",
  azul500: "#066fef",
  azul100: "#e7eefc",

  neutro900: "#151a29",
  neutro600: "#58607a",
  neutro400: "#9aa2b8",
  neutro300: "#d5dae6",
  neutro200: "#e6eaf3",
  neutro100: "#eef1f8",
  neutro50: "#f4f6fb",
  branco: "#ffffff",

  riscoAlto: "#b3261e",
  riscoAltoFundo: "#fbeae8",
  riscoMedio: "#a35a00",
  riscoMedioFundo: "#fcf0e2",
  riscoBaixo: "#58607a",
  riscoBaixoFundo: "#eef1f8",
  verdePositivo: "#0b7a5a",

  fundo: "#f4f6fb",
  superficie: "#ffffff",
  superficieSutil: "#f4f6fb",
  borda: "#d5dae6",
  texto: "#151a29",
  textoSuave: "#58607a",
  marca: "#00095b",
  marcaClara: "#066fef",
  erro: "#b3261e"
};

export const espaco = {
  0: 2,
  1: 4,
  2: 8,
  3: 12,
  4: 16,
  5: 24,
  6: 32,
  7: 48
};

export const texto = {
  "2xs": 11,
  xs: 12,
  sm: 13,
  md: 15,
  lg: 18,
  xl: 24,
  kpi: 36
};

export const peso = {
  medio: "600" as const,
  forte: "700" as const
};

export const raio = {
  sm: 6,
  md: 10,
  pilula: 999
};

export const fonteMonoEstilo = { fontFamily: "monospace" } as const;
export const fonteSerifItalicaEstilo = { fontFamily: "serif", fontStyle: "italic" as const };

export function corDoNivel(nivel: "alto" | "medio" | "baixo") {
  if (nivel === "alto") return { cor: cores.riscoAlto, fundo: cores.riscoAltoFundo };
  if (nivel === "medio") return { cor: cores.riscoMedio, fundo: cores.riscoMedioFundo };
  return { cor: cores.riscoBaixo, fundo: cores.riscoBaixoFundo };
}

export const CORES_SERIE = ["#00095b", "#c2410c", "#0b7a5a", "#6d28d9", "#0284c7", "#a16207"];
