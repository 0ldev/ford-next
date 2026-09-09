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
  loading?: boolean;
  /** Mensagem de erro; quando presente, substitui o número. */
  erro?: string | null;
  /** Habilita o botão de nova tentativa no estado de erro. */
  onTentarNovamente?: () => void;
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
  loading = false,
  erro = null,
  onTentarNovamente
}: KpiCardProps) {
  const temValor = typeof valor === "number" && Number.isFinite(valor);

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
        <div className="kpi-erro" role="alert">
          <p className="kpi-erro-mensagem">{erro}</p>
          {onTentarNovamente && (
            <button type="button" className="botao-secundario" onClick={onTentarNovamente}>
              Tentar novamente
            </button>
          )}
        </div>
      ) : loading || !temValor ? (
        // Barra cinza no lugar do número: ocupa o mesmo espaço do valor final.
        <div className="kpi-skeleton" role="status" aria-label={`Carregando ${label}`} />
      ) : (
        <p className="kpi-valor">
          {valorFormatado}
          <span className="kpi-unidade">{unidade}</span>
        </p>
      )}

      {/* Escondido durante o carregamento: o contexto vem do dado anterior e
          mostrá-lo ao lado do skeleton exibiria números do filtro antigo. */}
      {contexto && !erro && !loading && <p className="kpi-contexto">{contexto}</p>}
    </div>
  );
}

/** Formata inteiros no padrão pt-BR (separador de milhar com ponto). */
export function formatarInteiro(valor: number): string {
  return formatador.format(valor);
}
