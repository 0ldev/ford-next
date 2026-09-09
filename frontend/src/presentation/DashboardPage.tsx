import { useCallback, useState } from "react";
import type { VinShareFiltros } from "../domain/types";
import FiltrosBar from "./FiltrosBar";

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
 * mudanças, e as seções de KPI, gráficos e leads vão consumir este mesmo
 * estado nos próximos blocos, garantindo que a tela inteira fale do mesmo
 * recorte de dados.
 */
export default function DashboardPage() {
  const [filtros, setFiltros] = useState<VinShareFiltros>({});

  const atualizarFiltros = useCallback((alteracao: Partial<VinShareFiltros>) => {
    setFiltros((atual) => limparVazios({ ...atual, ...alteracao }));
  }, []);

  const limparFiltros = useCallback(() => {
    setFiltros({});
  }, []);

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
          <FiltrosBar
            filtros={filtros}
            onChange={atualizarFiltros}
            onLimpar={limparFiltros}
          />
          {/* Provisório: confirma visualmente que os filtros combinam sem conflito.
              Removido no Bloco 3, quando o KPI passar a consumir este estado. */}
          <details className="depuracao">
            <summary className="depuracao-titulo">Estado dos filtros (provisório)</summary>
            <pre className="depuracao-json">{JSON.stringify(filtros, null, 2)}</pre>
          </details>
        </section>

        <section className="secao" aria-labelledby="secao-kpi">
          <h2 className="secao-titulo" id="secao-kpi">
            Indicadores
          </h2>
          <p className="placeholder">KPI de VIN Share estimado em breve (Bloco 3).</p>
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
