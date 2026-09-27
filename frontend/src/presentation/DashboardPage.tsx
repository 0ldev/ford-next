import { useCallback, useEffect, useRef, useState } from "react";
import { useAnomaliesData } from "../application/useAnomaliesData";
import { useCatalogo } from "../application/useCatalogo";
import { useVinShareData } from "../application/useVinShareData";
import type { VinShareFiltros } from "../domain/types";
import AcaoPrioritariaKpiCard from "./AcaoPrioritariaKpiCard";
import AnomaliasPanel from "./AnomaliasPanel";
import FiltrosBar from "./FiltrosBar";
import KpiCard, { formatarInteiro, type ComparacaoKpi } from "./KpiCard";
import LeadsTable from "./LeadsTable";
import ResumoExecutivoSection from "./ResumoExecutivoSection";
import ResumoFiltros from "./ResumoFiltros";
import ScoreDistributionChart from "./ScoreDistributionChart";
import TrendChart from "./TrendChart";
import VinShareConcessionariaChart from "./VinShareConcessionariaChart";
import VinShareModeloChart from "./VinShareModeloChart";

/** Remove chaves com valor `undefined`/"" para o estado refletir só o que está de fato filtrado. */
function limparVazios(filtros: VinShareFiltros): VinShareFiltros {
  const resultado: VinShareFiltros = {};
  for (const [chave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== "") {
      resultado[chave as keyof VinShareFiltros] = valor;
    }
  }
  return resultado;
}

/**
 * "2020-01-03" (filtro de período, data ISO completa) vira "2020-01" — a
 * competência que `GET /api/trend` espera (mês, não dia; ver `TrendFiltros`).
 */
function paraCompetencia(dataIso?: string): string | undefined {
  return dataIso?.slice(0, 7);
}

/**
 * Página principal do VIN Share Intelligence Hub.
 *
 * Dona do estado dos filtros cruzados: a barra de filtros só reporta
 * mudanças, e as seções de KPI, gráficos e leads consomem este mesmo estado,
 * garantindo que a tela inteira fale do mesmo recorte de dados.
 */
export default function DashboardPage() {
  const [filtros, setFiltros] = useState<VinShareFiltros>({});
  const { data, loading, error, recarregar } = useVinShareData(filtros);
  const { data: catalogo } = useCatalogo();

  /*
   * Período default = intervalo real de dados (via `catalogo.periodoDisponivel`),
   * aplicado uma única vez assim que o catálogo chega — sem isso o KPI abre
   * comparando "todo o histórico com ele mesmo" (100%, sempre), porque o
   * elegível já vem do próprio histórico de serviços. Só entra se o usuário
   * ainda não tiver mexido no período (senão sobrescreveria uma escolha dele
   * ao catálogo recarregar).
   */
  const periodoPadraoAplicado = useRef(false);
  useEffect(() => {
    if (periodoPadraoAplicado.current || !catalogo?.periodoDisponivel) return;
    periodoPadraoAplicado.current = true;

    setFiltros((atual) =>
      atual.periodoInicio || atual.periodoFim
        ? atual
        : {
            ...atual,
            periodoInicio: catalogo.periodoDisponivel!.inicio,
            periodoFim: catalogo.periodoDisponivel!.fim
          }
    );
  }, [catalogo]);

  /*
   * Recorte da rede inteira (sem concessionária/modelo/idade/tipo de serviço),
   * mas no MESMO período do recorte principal — sem isso a régua compararia
   * períodos diferentes (ex.: recorte de 3 meses vs. rede em todo o histórico)
   * e a diferença em pontos percentuais não diria nada de real. Serve de régua:
   * sem ela, "30,7% nesta concessionária" não diz se está bem ou mal.
   */
  const { data: referencia } = useVinShareData({
    periodoInicio: filtros.periodoInicio,
    periodoFim: filtros.periodoFim
  });

  const {
    data: anomalias,
    loading: carregandoAnomalias,
    error: erroAnomalias,
    recarregar: recarregarAnomalias
  } = useAnomaliesData();

  const atualizarFiltros = useCallback((alteracao: Partial<VinShareFiltros>) => {
    setFiltros((atual) => limparVazios({ ...atual, ...alteracao }));
  }, []);

  const limparFiltros = useCallback(() => {
    setFiltros({});
  }, []);

  /*
   * Atalho vindo do painel de anomalias: aplica o recorte e sobe a página,
   * para quem está assistindo ver o dashboard inteiro reagir ao alerta.
   */
  const filtrarPelaAnomalia = useCallback((filtro: Partial<VinShareFiltros>) => {
    setFiltros((atual) => limparVazios({ ...atual, ...filtro }));

    const suave = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: suave ? "smooth" : "auto" });
  }, []);

  /*
   * Período sozinho não conta como "recorte" pra fins da régua: ele agora vem
   * preenchido por padrão (`periodoPadraoAplicado` acima), então
   * concessionária/modelo/idade/tipo de serviço são o que de fato distingue o
   * recorte principal da referência de rede — comparar a rede com ela mesma
   * (mesmo período, nenhum outro filtro) seria ruído.
   */
  const temFiltroDemografico = Boolean(
    filtros.concessionaria || filtros.modelo || filtros.faixaIdade || filtros.tipoServico
  );

  const comparacao: ComparacaoKpi | undefined =
    temFiltroDemografico && referencia
      ? { base: referencia.vinShareEstimado, rotuloBase: "média da rede" }
      : undefined;

  const contexto = data
    ? `${formatarInteiro(data.totalComServico)} de ${formatarInteiro(
        data.totalVeiculosElegiveis
      )} veículos elegíveis passaram pela rede oficial`
    : undefined;

  return (
    <div className="pagina">
      <header className="cabecalho">
        <div className="marca">
          <span className="marca-selo" aria-hidden="true">
            Ford
          </span>
          <div>
            <h1 className="cabecalho-titulo">VIN Share Intelligence Hub</h1>
            <p className="cabecalho-subtitulo">
              Retenção de pós-venda da rede Ford: onde o VIN Share está caindo, por que, e quem
              contatar primeiro.
            </p>
          </div>
        </div>
      </header>

      <main className="conteudo">
        <section className="secao" aria-labelledby="secao-filtros">
          <h2 className="secao-titulo" id="secao-filtros">
            Filtros
          </h2>
          <FiltrosBar
            filtros={filtros}
            onChange={atualizarFiltros}
            onLimpar={limparFiltros}
            catalogo={catalogo}
          />
          <ResumoFiltros filtros={filtros} />
        </section>

        <section className="secao" aria-labelledby="secao-kpi">
          <h2 className="secao-titulo" id="secao-kpi">
            Indicadores
          </h2>
          <div className="indicadores">
            <KpiCard
              label="VIN Share estimado"
              valor={data?.vinShareEstimado}
              contexto={contexto}
              comparacao={comparacao}
              loading={loading}
              erro={error ? error.message : null}
              onTentarNovamente={recarregar}
            />

            <KpiCard
              label="Anomalias detectadas"
              valor={anomalias?.length}
              unidade=""
              casasDecimais={0}
              loading={carregandoAnomalias}
              erro={erroAnomalias ? erroAnomalias.message : null}
              onTentarNovamente={recarregarAnomalias}
            />

            <AcaoPrioritariaKpiCard concessionaria={filtros.concessionaria} />
          </div>
        </section>

        <section className="secao" aria-labelledby="secao-tendencia">
          <h2 className="secao-titulo" id="secao-tendencia">
            Tendência de VIN Share
          </h2>
          <TrendChart
            periodoInicio={paraCompetencia(filtros.periodoInicio)}
            periodoFim={paraCompetencia(filtros.periodoFim)}
            modelos={catalogo?.modelos ?? []}
          />
        </section>

        <section className="secao" aria-labelledby="secao-ranking-modelo">
          <h2 className="secao-titulo" id="secao-ranking-modelo">
            VIN Share por modelo
          </h2>
          <VinShareModeloChart
            periodoInicio={paraCompetencia(filtros.periodoInicio)}
            periodoFim={paraCompetencia(filtros.periodoFim)}
          />
        </section>

        <section className="secao" aria-labelledby="secao-ranking-concessionaria">
          <h2 className="secao-titulo" id="secao-ranking-concessionaria">
            VIN Share por concessionária
          </h2>
          <VinShareConcessionariaChart />
        </section>

        <section className="secao" aria-labelledby="secao-distribuicao-score">
          <h2 className="secao-titulo" id="secao-distribuicao-score">
            Distribuição de score de risco
          </h2>
          <ScoreDistributionChart />
        </section>

        <section className="secao" aria-labelledby="secao-anomalias">
          <h2 className="secao-titulo" id="secao-anomalias">
            Anomalias detectadas
          </h2>
          <AnomaliasPanel onFiltrar={filtrarPelaAnomalia} />
        </section>

        <section className="secao" aria-labelledby="secao-leads">
          <h2 className="secao-titulo" id="secao-leads">
            Leads priorizados
          </h2>
          <LeadsTable concessionaria={filtros.concessionaria} />
        </section>

        <section className="secao" aria-labelledby="secao-resumo-executivo">
          <h2 className="secao-titulo" id="secao-resumo-executivo">
            Resumo executivo
          </h2>
          <p className="secao-subtitulo">Onde agir primeiro, em um único olhar.</p>
          <ResumoExecutivoSection />
        </section>
      </main>
    </div>
  );
}
