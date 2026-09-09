export interface SeletorModelosProps {
  /** Todos os modelos disponíveis. */
  opcoes: readonly string[];
  /** Modelos marcados; vazio significa "todos". */
  selecionados: string[];
  onChange: (selecionados: string[]) => void;
}

/**
 * Seleção múltipla de modelos para o gráfico de tendência.
 *
 * Diferente do `Dropdown` da barra de filtros (seleção única), aqui o gestor
 * compara várias séries ao mesmo tempo. Nenhum marcado equivale a todos
 * marcados — evita o gráfico vazio, que não diz nada.
 */
export default function SeletorModelos({
  opcoes,
  selecionados,
  onChange
}: SeletorModelosProps) {
  const nenhumMarcado = selecionados.length === 0;

  const alternar = (modelo: string) => {
    onChange(
      selecionados.includes(modelo)
        ? selecionados.filter((item) => item !== modelo)
        : [...selecionados, modelo]
    );
  };

  return (
    <fieldset className="seletor-modelos">
      <legend className="campo-label">Modelos no gráfico</legend>

      <div className="seletor-modelos-opcoes">
        {opcoes.map((modelo) => (
          <label key={modelo} className="checkbox">
            <input
              type="checkbox"
              checked={selecionados.includes(modelo)}
              onChange={() => alternar(modelo)}
            />
            <span>{modelo}</span>
          </label>
        ))}

        <button
          type="button"
          className="botao-link"
          onClick={() => onChange([])}
          disabled={nenhumMarcado}
        >
          Mostrar todos
        </button>
      </div>

      {nenhumMarcado && (
        <p className="seletor-modelos-dica">Nenhum modelo marcado: exibindo todos.</p>
      )}
    </fieldset>
  );
}
