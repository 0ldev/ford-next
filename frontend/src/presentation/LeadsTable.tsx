import { useEffect, useMemo, useState } from "react";
import { useAcoesRecomendadas } from "../application/useAcoesRecomendadas";
import { useLeads } from "../application/useLeads";
import { encontrarLeadPrioritario } from "../domain/leads";
import { LIMIAR_ALTO, LIMIAR_MEDIO, nivelDeRisco } from "../domain/severidade";
import type { Lead } from "../domain/types";
import { rotuloDaConcessionaria } from "../infrastructure/mockData";
import AcaoPrioritaria from "./AcaoPrioritaria";
import BotaoCopiar from "./BotaoCopiar";
import Dropdown, { type DropdownOption } from "./Dropdown";
import EstadoErro from "./EstadoErro";
import { ROTULO_ACAO } from "./rotulos";

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

/*
 * "Alto" é o topo aberto da distribuição (sem teto — >= 70% já é o fim da escala).
 * "Médio" precisa de teto: sem ele, um piso sozinho (score >= 30%) ainda inclui os
 * ~97 mil VINs empatados em 100%, e a tela mostraria "risco médio" com o mesmo
 * badge vermelho de "alto" — o filtro parecia não fazer nada. O teto isola a
 * banda de verdade (30% a 69%), a mesma faixa que os badges de severidade (ver
 * `nivelDeRisco`) já pintam de âmbar.
 */
const TETO_FAIXA: Partial<Record<FaixaScore, number>> = {
  medio: LIMIAR_ALTO
};

const OPCOES_FAIXA: DropdownOption[] = [
  {
    value: "medio",
    label: `Risco médio (${Math.round(LIMIAR_MEDIO * 100)}% a ${Math.round(LIMIAR_ALTO * 100) - 1}%)`
  },
  { value: "alto", label: `Risco alto (≥ ${Math.round(LIMIAR_ALTO * 100)}%)` }
];

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
 * A "Faixa de risco" vira `scoreMinimo` na requisição — filtrar no servidor
 * (não só na página já buscada) é o que faz a fila trazer leads de fato fora
 * do topo empatado em 100%, em vez de só reordenar a mesma fatia. A ordenação
 * asc/desc, essa sim, é client-side dentro da página atual: o gestor inverte
 * a leitura sem esperar a rede. A ação recomendada de cada veículo é buscada
 * só quando a linha é expandida.
 */
export default function LeadsTable({ concessionaria }: LeadsTableProps) {
  const [ordem, setOrdem] = useState<Ordem>("desc");
  const [faixa, setFaixa] = useState<FaixaScore | undefined>(undefined);
  const [pagina, setPagina] = useState(1);
  const [expandidos, setExpandidos] = useState<string[]>([]);

  const piso = faixa ? PISO_FAIXA[faixa] : undefined;
  const teto = faixa ? TETO_FAIXA[faixa] : undefined;
  const { data, loading, error, recarregar } = useLeads({
    concessionaria,
    scoreMinimo: piso,
    scoreMaximo: teto,
    pagina
  });
  const { acoes, carregar, recarregar: recarregarAcao } = useAcoesRecomendadas();

  // Trocar de concessionária ou de faixa muda o recorte inteiro — a página
  // antiga pode nem existir mais nele, então volta pro início.
  useEffect(() => {
    setPagina(1);
  }, [concessionaria, faixa]);

  const total = data?.total ?? 0;
  const tamanhoPagina = data?.tamanhoPagina ?? 50;
  const totalPaginas = Math.max(1, Math.ceil(total / tamanhoPagina));

  const leads = useMemo(() => {
    const lista = data?.leads ?? [];
    return [...lista].sort((a, b) => (ordem === "desc" ? b.score - a.score : a.score - b.score));
  }, [data, ordem]);

  /*
   * O card de destaque mostra sempre o caso mais urgente do recorte, então
   * olha o maior score e não o primeiro da lista — inverter a ordenação da
   * tabela não deve trocar qual é a ação prioritária.
   */
  const leadPrioritario = useMemo(() => encontrarLeadPrioritario(leads), [leads]);

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
      <AcaoPrioritaria
        lead={leadPrioritario}
        concessionaria={
          leadPrioritario ? rotuloDaConcessionaria(leadPrioritario.dealerCode) : ""
        }
        acao={leadPrioritario ? acoes[leadPrioritario.vin] : undefined}
        onCarregar={carregar}
        onTentarNovamente={recarregarAcao}
      />

      <div className="leads-controles">
        <Dropdown
          label="Faixa de risco"
          options={OPCOES_FAIXA}
          value={faixa}
          onChange={(valor) => setFaixa(valor as FaixaScore | undefined)}
          placeholder="Todos os scores"
        />
        <p className="leads-contagem">
          {total} {total === 1 ? "lead" : "leads"}{faixa ? " nesta faixa" : " na fila"}
        </p>
      </div>

      {leads.length === 0 ? (
        <p className="lista-vazia">Nenhum lead encontrado para este filtro.</p>
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

      {totalPaginas > 1 && (
        <div className="leads-paginacao">
          <button
            type="button"
            className="botao-paginacao"
            onClick={() => setPagina((atual) => atual - 1)}
            disabled={pagina <= 1}
          >
            ← Anterior
          </button>
          <span className="leads-paginacao-texto">
            Página {pagina} de {totalPaginas}
          </span>
          <button
            type="button"
            className="botao-paginacao"
            onClick={() => setPagina((atual) => atual + 1)}
            disabled={pagina >= totalPaginas}
          >
            Próxima →
          </button>
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
        <td>{rotuloDaConcessionaria(lead.dealerCode)}</td>
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
                    <BotaoCopiar texto={acao.data.mensagem} />
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
