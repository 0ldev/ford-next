const formatadorInteiro = new Intl.NumberFormat("pt-BR");

export function formatarInteiro(valor: number): string {
  return formatadorInteiro.format(valor);
}

export function formatarComCasas(valor: number, casas = 1): string {
  return valor.toLocaleString("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas
  });
}

export function formatarPercentual(valor: number, casas = 1): string {
  return `${formatarComCasas(valor, casas)}%`;
}

export function formatarDataBR(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : iso;
}

export function encurtarVin(vin: string): string {
  return vin.length > 12 ? `${vin.slice(0, 12)}…` : vin;
}

export function vinCurto(vin: string): string {
  return vin.slice(0, 8).toUpperCase();
}
