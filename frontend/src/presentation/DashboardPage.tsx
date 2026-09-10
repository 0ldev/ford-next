import { useCallback, useState } from "react";
import { useVinShareData } from "../application/useVinShareData";
import type { VinShareFiltros } from "../domain/types";
import AnomaliasPanel from "./AnomaliasPanel";
import FiltrosBar from "./FiltrosBar";
import KpiCard, { formatarInteiro, type ComparacaoKpi } from "./KpiCard";
import LeadsTable from "./LeadsTable";
import ResumoFiltros from "./ResumoFiltros";
import TrendChart from "./TrendChart";

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
 * Página principal do VIN Share Intelligence Hub.
 *
 * Dona do estado dos filtros cruzados: a barra de filtros só reporta
 * mudanças, e as seções de KPI, gráficos e leads consomem este mesmo estado,
 * garantindo que a tela inteira fale do mesmo recorte de dados.
 */
export default function DashboardPage() {
  const [filtros, setFiltros] = useState<VinShareFiltros>({});
  const { data, loading, error, recarregar } = useVinShareData(filtros);

  /*
   * Recorte da rede inteira, buscado uma vez só (a chave do hook é constante,
   * então não refaz a requisição a cada filtro). Serve de régua: sem ela,
   * "30,7% nesta concessionária" não diz se está bem ou mal.
   */
  const { data: referencia } = useVinShareData({});

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

  const temFiltroAtivo = Object.keys(filtros).length > 0;

  /* A régua só aparece quando há recorte: comparar a rede com ela mesma seria ruído. */
  const comparacao: ComparacaoKpi | undefined =
    temFiltroAtivo && referencia
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
        <h1 className="cabecalho-titulo">VIN Share Intelligence Hub</h1>
        <p className="cabecalho-subtitulo">
          Retenção de pós-venda da rede Ford: onde o VIN Share está caindo, por que, e quem
          contatar primeiro.
        </p>
      </header>

      <main className="conteudo">
        <section className="secao" aria-labelledby="secao-filtros">
          <h2 className="secao-titulo" id="secao-filtros">
            Filtros
          </h2>
          <FiltrosBar filtros={filtros} onChange={atualizarFiltros} onLimpar={limparFiltros} />
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
          </div>
        </section>

        <section className="secao" aria-labelledby="secao-tendencia">
          <h2 className="secao-titulo" id="secao-tendencia">
            Tendência de VIN Share
          </h2>
          <TrendChart
            periodoInicio={filtros.periodoInicio}
            periodoFim={filtros.periodoFim}
          />
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
      </main>
    </div>
  );
}
