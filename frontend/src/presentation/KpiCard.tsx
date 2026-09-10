import EstadoErro from "./EstadoErro";

export interface KpiCardProps {
  /** Rótulo do indicador, ex.: "VIN Share estimado". */
  label: string;
  /** Valor do indicador; `null`/`undefined` enquanto não há dado. */
  valor?: number | null;
  /** Sufixo da unidade exibido ao lado do número. */
  unidade?: string;
  /** Casas decimais na formatação pt-BR. */
  casasDecimais?: number;
  /** Linha de contexto abaixo do número, ex.: "1.240 de 2.100 veículos elegíveis". */
  contexto?: string;
  /** Referência para o leitor saber se o número é bom ou ruim. */
  comparacao?: ComparacaoKpi;
  loading?: boolean;
  /** Mensagem de erro; quando presente, substitui o número. */
  erro?: string | null;
  /** Habilita o botão de nova tentativa no estado de erro. */
  onTentarNovamente?: () => void;
}

export interface ComparacaoKpi {
  /** Valor de referência, na mesma unidade do indicador. */
  base: number;
  /** O que a referência representa; a frase já traz o "da" antes, ex.: "média da rede". */
  rotuloBase: string;
}

const formatador = new Intl.NumberFormat("pt-BR");

/**
 * Card de indicador do dashboard.
 *
 * Cobre os três estados de uma requisição — carregando, erro e sucesso —
 * mantendo a mesma altura, para a página não pular quando o dado chega.
 */
export default function KpiCard({
  label,
  valor,
  unidade = "%",
  casasDecimais = 1,
  contexto,
  comparacao,
  loading = false,
  erro = null,
  onTentarNovamente
}: KpiCardProps) {
  const temValor = typeof valor === "number" && Number.isFinite(valor);

  /*
   * Sozinho, "34,7%" não diz se é bom ou ruim. A diferença em pontos
   * percentuais contra a referência é o que transforma o número em juízo.
   */
  const diferenca = temValor && comparacao ? valor - comparacao.base : null;
  const sentido = diferenca === null ? null : diferenca >= 0 ? "acima" : "abaixo";

  const valorFormatado = temValor
    ? valor.toLocaleString("pt-BR", {
        minimumFractionDigits: casasDecimais,
        maximumFractionDigits: casasDecimais
      })
    : null;

  return (
    <div className="kpi" aria-busy={loading}>
      <span className="kpi-label">{label}</span>

      {erro ? (
        <EstadoErro mensagem={erro} onTentarNovamente={onTentarNovamente} />
      ) : loading || !temValor ? (
        // Barra cinza no lugar do número: ocupa o mesmo espaço do valor final.
        <div className="kpi-skeleton" role="status" aria-label={`Carregando ${label}`} />
      ) : (
        <p className="kpi-valor">
          {valorFormatado}
          <span className="kpi-unidade">{unidade}</span>
        </p>
      )}

      {comparacao && diferenca !== null && sentido && !erro && !loading && (
        <p className={`kpi-comparacao kpi-comparacao-${sentido}`}>
          <span aria-hidden="true">{sentido === "acima" ? "▲" : "▼"}</span>
          {formatarPontos(Math.abs(diferenca))} p.p. {sentido} da {comparacao.rotuloBase} (
          {formatarPontos(comparacao.base)}%)
        </p>
      )}

      {/* Escondido durante o carregamento: o contexto vem do dado anterior e
          mostrá-lo ao lado do skeleton exibiria números do filtro antigo. */}
      {contexto && !erro && !loading && <p className="kpi-contexto">{contexto}</p>}
    </div>
  );
}

/** Uma casa decimal, vírgula decimal — o mesmo formato do número grande. */
function formatarPontos(valor: number): string {
  return valor.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });
}

/** Formata inteiros no padrão pt-BR (separador de milhar com ponto). */
export function formatarInteiro(valor: number): string {
  return formatador.format(valor);
}
