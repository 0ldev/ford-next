import { useAnomaliesData } from "../application/useAnomaliesData";
import type { Anomaly, AnomalyTipo } from "../domain/types";
import AnomaliaItem from "./AnomaliaItem";

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
      <div className="painel-estado" role="alert">
        <p className="mensagem-erro">{error.message}</p>
        <button type="button" className="botao-secundario" onClick={recarregar}>
          Tentar novamente
        </button>
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

  return (
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
              <p className="anomalias-vazio">Nenhuma anomalia neste grupo.</p>
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
  );
}
