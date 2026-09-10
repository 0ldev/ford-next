import { useAnomaliesData } from "../application/useAnomaliesData";
import type { Anomaly, AnomalyTipo } from "../domain/types";
import AnomaliaItem from "./AnomaliaItem";
import EstadoErro from "./EstadoErro";

/** Os três grupos do painel, na ordem em que o gestor deve olhar. */
const GRUPOS: { tipo: AnomalyTipo; titulo: string; descricao: string }[] = [
  {
    tipo: "queda_dealer",
    titulo: "Quedas abruptas por concessionária",
    descricao: "Unidades perdendo retenção rápido demais para ser sazonalidade."
  },
  {
    tipo: "gap_modelo",
    titulo: "Gap crescente por modelo",
    descricao: "Modelos que se afastam da média de VIN Share da rede."
  },
  {
    tipo: "pico_mainsource",
    titulo: "Picos incomuns de origem",
    descricao: "Serviços migrando para fora da rede oficial."
  }
];

/**
 * Painel de anomalias detectadas.
 *
 * Os três grupos aparecem sempre, mesmo vazios: um grupo ausente da tela
 * seria lido como "não verificamos isso", quando o certo é "verificamos e
 * não há nada".
 */
export default function AnomaliasPanel() {
  const { data, loading, error, recarregar } = useAnomaliesData();

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
        <p className="placeholder-texto">Carregando anomalias…</p>
      </div>
    );
  }

  const anomalias: Anomaly[] = data ?? [];

  /*
   * O painel lista seis anomalias; numa demonstração ninguém compara seis
   * severidades de cabeça. Esta linha diz de saída qual é a pior, a partir
   * do mesmo dado já carregado — sem busca nova.
   */
  const maisSevera = anomalias.reduce<Anomaly | undefined>(
    (pior, atual) => (!pior || atual.severidade > pior.severidade ? atual : pior),
    undefined
  );

  return (
    <>
      {maisSevera && (
        <p className="destaque-anomalia">
          <span className="destaque-anomalia-rotulo">
            Maior alerta · {Math.round(maisSevera.severidade * 100)}% de severidade
          </span>
          <strong className="destaque-anomalia-entidade">{maisSevera.entidade}</strong>
          <span className="destaque-anomalia-descricao">{maisSevera.descricao}</span>
        </p>
      )}

      <div className="anomalias">
        {GRUPOS.map((grupo) => {
          const doGrupo = anomalias
            .filter((anomalia) => anomalia.tipo === grupo.tipo)
            .sort((a, b) => b.severidade - a.severidade);

          return (
            <section className="anomalias-grupo" key={grupo.tipo}>
              <h3 className="anomalias-grupo-titulo">
                {grupo.titulo}
                <span className="anomalias-grupo-contagem">{doGrupo.length}</span>
              </h3>
              <p className="anomalias-grupo-descricao">{grupo.descricao}</p>

              {doGrupo.length === 0 ? (
                <p className="lista-vazia">Nenhuma anomalia neste grupo.</p>
              ) : (
                <ul className="anomalias-lista">
                  {doGrupo.map((anomalia) => (
                    <AnomaliaItem
                      key={`${anomalia.tipo}-${anomalia.entidade}`}
                      anomalia={anomalia}
                    />
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </>
  );
}
