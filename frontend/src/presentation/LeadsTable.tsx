import { useMemo, useState } from "react";
import { useAcoesRecomendadas } from "../application/useAcoesRecomendadas";
import { useLeads } from "../application/useLeads";
import { LIMIAR_ALTO, LIMIAR_MEDIO, nivelDeRisco } from "../domain/severidade";
import type { AcaoTipo, Lead } from "../domain/types";
import { CONCESSIONARIAS } from "../infrastructure/mockData";
import Dropdown, { type DropdownOption } from "./Dropdown";
import EstadoErro from "./EstadoErro";

export interface LeadsTableProps {
  /** dealerCode vindo da barra de filtros; ausente traz a fila da rede toda. */
  concessionaria?: string;
}

type Ordem = "asc" | "desc";
type FaixaScore = "medio" | "alto";

const PISO_FAIXA: Record<FaixaScore, number> = {
  medio: LIMIAR_MEDIO,
  alto: LIMIAR_ALTO
};

const OPCOES_FAIXA: DropdownOption[] = [
  { value: "medio", label: `Risco médio ou maior (≥ ${Math.round(LIMIAR_MEDIO * 100)}%)` },
  { value: "alto", label: `Risco alto (≥ ${Math.round(LIMIAR_ALTO * 100)}%)` }
];

const ROTULO_ACAO: Record<AcaoTipo, string> = {
  contato_ativo: "Contato ativo",
  oferta: "Oferta dirigida",
  lembrete: "Lembrete automático"
};

/** Nome legível da concessionária; cai no código quando não conhecemos o nome. */
function nomeDaConcessionaria(dealerCode: string): string {
  return CONCESSIONARIAS.find((item) => item.dealerCode === dealerCode)?.nome ?? dealerCode;
}

function formatarScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

/** VIN é um hash de 40 caracteres; a tabela mostra o prefixo e guarda o resto no title. */
function encurtarVin(vin: string): string {
  return vin.length > 12 ? `${vin.slice(0, 12)}…` : vin;
}

/**
 * Prefixo curto para leitura em voz alta. Soletrar os 40 caracteres do hash
 * não ajuda ninguém; os 8 primeiros identificam a linha e casam com o que a
 * tabela mostra.
 */
function vinParaLeitura(vin: string): string {
  return vin.length > 8 ? `${vin.slice(0, 8)}, abreviado` : vin;
}

/**
 * Fila de leads priorizada por risco de evasão.
 *
 * Ordenação e filtro são client-side, sobre os dados já buscados: o gestor
 * reorganiza a fila sem esperar a rede. A ação recomendada de cada veículo
 * é buscada só quando a linha é expandida.
 */
export default function LeadsTable({ concessionaria }: LeadsTableProps) {
  const { data, loading, error, recarregar } = useLeads({ concessionaria });
  const { acoes, carregar, recarregar: recarregarAcao } = useAcoesRecomendadas();

  const [ordem, setOrdem] = useState<Ordem>("desc");
  const [faixa, setFaixa] = useState<FaixaScore | undefined>(undefined);
  const [expandidos, setExpandidos] = useState<string[]>([]);

  const leads = useMemo(() => {
    const lista = data ?? [];
    const piso = faixa ? PISO_FAIXA[faixa] : 0;

    return lista
      .filter((lead) => lead.score >= piso)
      .sort((a, b) => (ordem === "desc" ? b.score - a.score : a.score - b.score));
  }, [data, faixa, ordem]);

  const alternarLinha = (vin: string) => {
    setExpandidos((atual) =>
      atual.includes(vin) ? atual.filter((item) => item !== vin) : [...atual, vin]
    );
    // O hook ignora VINs já buscados, então reabrir não gera nova requisição.
    carregar(vin);
  };

  if (error) {
    return (
      <div className="painel-estado">
        <EstadoErro mensagem={error.message} onTentarNovamente={recarregar} />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="painel-estado" role="status">
        <p className="placeholder-texto">Carregando leads…</p>
      </div>
    );
  }

  return (
    <div className="leads">
      <div className="leads-controles">
        <Dropdown
          label="Faixa de risco"
          options={OPCOES_FAIXA}
          value={faixa}
          onChange={(valor) => setFaixa(valor as FaixaScore | undefined)}
          placeholder="Todos os scores"
        />
        <p className="leads-contagem">
          {leads.length} {leads.length === 1 ? "lead" : "leads"}
          {faixa ? ` de ${data?.length ?? 0} na fila` : ""}
        </p>
      </div>

      {leads.length === 0 ? (
        <p className="lista-vazia">Nenhum lead nesta faixa de risco.</p>
      ) : (
        <div className="tabela-rolagem">
          <table className="tabela">
            <thead>
              <tr>
                <th scope="col" className="coluna-expandir">
                  <span className="sr-only">Detalhes</span>
                </th>
                <th scope="col">VIN</th>
                <th scope="col">Concessionária</th>
                <th scope="col">Modelo</th>
                <th
                  scope="col"
                  aria-sort={ordem === "desc" ? "descending" : "ascending"}
                  className="coluna-score"
                >
                  <button
                    type="button"
                    className="cabecalho-ordenavel"
                    onClick={() => setOrdem((atual) => (atual === "desc" ? "asc" : "desc"))}
                  >
                    Score
                    <span aria-hidden="true" className="seta-ordem">
                      {ordem === "desc" ? "▼" : "▲"}
                    </span>
                  </button>
                </th>
                <th scope="col">Motivo</th>
              </tr>
            </thead>

            <tbody>
              {leads.map((lead) => (
                <LinhaLead
                  key={lead.vin}
                  lead={lead}
                  expandido={expandidos.includes(lead.vin)}
                  onAlternar={() => alternarLinha(lead.vin)}
                  acao={acoes[lead.vin]}
                  onTentarNovamente={() => recarregarAcao(lead.vin)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

interface LinhaLeadProps {
  lead: Lead;
  expandido: boolean;
  onAlternar: () => void;
  acao?: ReturnType<typeof useAcoesRecomendadas>["acoes"][string];
  onTentarNovamente: () => void;
}

function LinhaLead({ lead, expandido, onAlternar, acao, onTentarNovamente }: LinhaLeadProps) {
  const nivel = nivelDeRisco(lead.score);
  const idDetalhe = `detalhe-${lead.vin}`;

  return (
    <>
      <tr className={expandido ? "linha-expandida" : undefined}>
        <td className="coluna-expandir">
          <button
            type="button"
            className="botao-expandir"
            aria-expanded={expandido}
            aria-controls={idDetalhe}
            onClick={onAlternar}
          >
            <span aria-hidden="true">{expandido ? "−" : "+"}</span>
            <span className="sr-only">
              {expandido ? "Recolher" : "Expandir"} detalhes do VIN {vinParaLeitura(lead.vin)}
            </span>
          </button>
        </td>
        <td className="celula-vin" title={lead.vin}>
          {encurtarVin(lead.vin)}
        </td>
        <td>{nomeDaConcessionaria(lead.dealerCode)}</td>
        <td>{lead.modelo}</td>
        <td className="coluna-score">
          <span className={`score score-${nivel}`}>{formatarScore(lead.score)}</span>
        </td>
        <td className="celula-motivo">{lead.motivo}</td>
      </tr>

      {/* A linha existe sempre, oculta quando recolhida: assim o alvo do
          aria-controls do botão nunca é um id inexistente. O conteúdo, esse
          sim, só é montado quando a linha abre. */}
      <tr className="linha-detalhe" id={idDetalhe} hidden={!expandido}>
        <td colSpan={6}>
          {expandido && (
            <div className="detalhe">
              <div className="detalhe-bloco">
                <h4 className="detalhe-titulo">Motivo do risco</h4>
                <p className="detalhe-texto">{lead.motivo}</p>
              </div>

              <div className="detalhe-bloco">
                <h4 className="detalhe-titulo">Ação recomendada</h4>

                {!acao || acao.loading ? (
                  <p className="placeholder-texto" role="status">
                    Buscando ação recomendada…
                  </p>
                ) : acao.error ? (
                  <EstadoErro
                    mensagem={acao.error.message}
                    onTentarNovamente={onTentarNovamente}
                  />
                ) : acao.data ? (
                  <>
                    <span className={`selo-acao selo-acao-${acao.data.acao}`}>
                      {ROTULO_ACAO[acao.data.acao]}
                    </span>
                    <p className="detalhe-mensagem">{acao.data.mensagem}</p>
                  </>
                ) : null}
              </div>
            </div>
          )}
        </td>
      </tr>
    </>
  );
}
