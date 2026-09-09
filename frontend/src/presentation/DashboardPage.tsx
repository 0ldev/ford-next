import { useCallback, useState } from "react";
import { useVinShareData } from "../application/useVinShareData";
import type { VinShareFiltros } from "../domain/types";
import FiltrosBar from "./FiltrosBar";
import KpiCard, { formatarInteiro } from "./KpiCard";

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

  const atualizarFiltros = useCallback((alteracao: Partial<VinShareFiltros>) => {
    setFiltros((atual) => limparVazios({ ...atual, ...alteracao }));
  }, []);

  const limparFiltros = useCallback(() => {
    setFiltros({});
  }, []);

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
        </section>

        <section className="secao" aria-labelledby="secao-kpi">
          <h2 className="secao-titulo" id="secao-kpi">
            Indicadores
          </h2>
          <KpiCard
            label="VIN Share estimado"
            valor={data?.vinShareEstimado}
            contexto={contexto}
            loading={loading}
            erro={error ? error.message : null}
            onTentarNovamente={recarregar}
          />
        </section>

        <section className="secao" aria-labelledby="secao-graficos">
          <h2 className="secao-titulo" id="secao-graficos">
            Tendência e anomalias
          </h2>
          <p className="placeholder">
            Gráfico de tendência temporal e painel de anomalias em breve (Bloco 4).
          </p>
        </section>

        <section className="secao" aria-labelledby="secao-leads">
          <h2 className="secao-titulo" id="secao-leads">
            Leads priorizados
          </h2>
          <p className="placeholder">
            Tabela de leads com ação recomendada em breve (Bloco 5).
          </p>
        </section>
      </main>
    </div>
  );
}
