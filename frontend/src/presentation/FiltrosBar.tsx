import { useId, useMemo } from "react";
import type { Catalogo, VinShareFiltros } from "../domain/types";
import { FAIXAS_IDADE, rotuloDaConcessionaria } from "../infrastructure/mockData";
import Dropdown, { type DropdownOption } from "./Dropdown";

export interface FiltrosBarProps {
  filtros: VinShareFiltros;
  /** Recebe apenas os campos alterados; a página faz o merge no estado. */
  onChange: (alteracao: Partial<VinShareFiltros>) => void;
  onLimpar: () => void;
  /**
   * Catálogo real (via `useCatalogo`), não uma lista fixa no frontend — assim
   * os dropdowns nunca divergem do que a API realmente tem.
   */
  catalogo: Catalogo | null;
}

const OPCOES_FAIXA_IDADE: DropdownOption[] = FAIXAS_IDADE.map((faixa) => ({
  value: faixa.value,
  label: faixa.label
}));

/** Converte "" (campo de data limpo pelo usuário) em `undefined`. */
function normalizarData(valor: string): string | undefined {
  return valor === "" ? undefined : valor;
}

/**
 * Barra de filtros cruzados do dashboard.
 *
 * Todos os filtros são combináveis e escrevem no mesmo estado centralizado
 * em `DashboardPage`; nenhum deles guarda estado próprio.
 */
export default function FiltrosBar({ filtros, onChange, onLimpar, catalogo }: FiltrosBarProps) {
  const idInicio = useId();
  const idFim = useId();

  const algumFiltroAtivo = Object.values(filtros).some(
    (valor) => valor !== undefined && valor !== ""
  );

  const opcoesConcessionaria: DropdownOption[] = useMemo(
    () =>
      (catalogo?.concessionarias ?? []).map((dealerCode) => {
        const nome = rotuloDaConcessionaria(dealerCode);
        // Sem nome real (API real, dataset não tem cadastro de nomes de
        // concessionária): mostra só o código, em vez de "100 — 100".
        return { value: dealerCode, label: nome === dealerCode ? dealerCode : `${dealerCode} — ${nome}` };
      }),
    [catalogo]
  );

  const opcoesModelo: DropdownOption[] = useMemo(
    () => (catalogo?.modelos ?? []).map((modelo) => ({ value: modelo, label: modelo })),
    [catalogo]
  );

  const opcoesTipoServico: DropdownOption[] = useMemo(
    () => (catalogo?.tiposServico ?? []).map((tipo) => ({ value: tipo, label: tipo })),
    [catalogo]
  );

  return (
    <div className="filtros">
      <div className="filtros-campos">
        <Dropdown
          label="Concessionária"
          options={opcoesConcessionaria}
          value={filtros.concessionaria}
          onChange={(concessionaria) => onChange({ concessionaria })}
          placeholder="Todas"
        />

        <Dropdown
          label="Modelo"
          options={opcoesModelo}
          value={filtros.modelo}
          onChange={(modelo) => onChange({ modelo })}
        />

        <Dropdown
          label="Idade do veículo"
          options={OPCOES_FAIXA_IDADE}
          value={filtros.faixaIdade}
          onChange={(faixaIdade) => onChange({ faixaIdade })}
          placeholder="Todas as idades"
        />

        <Dropdown
          label="Tipo de serviço"
          options={opcoesTipoServico}
          value={filtros.tipoServico}
          onChange={(tipoServico) => onChange({ tipoServico })}
        />

        <div className="campo">
          <label className="campo-label" htmlFor={idInicio}>
            Período — início
          </label>
          <input
            id={idInicio}
            className="campo-controle"
            type="date"
            value={filtros.periodoInicio ?? ""}
            // Impede montar um intervalo invertido pela própria UI do navegador.
            max={filtros.periodoFim}
            onChange={(evento) =>
              onChange({ periodoInicio: normalizarData(evento.target.value) })
            }
          />
        </div>

        <div className="campo">
          <label className="campo-label" htmlFor={idFim}>
            Período — fim
          </label>
          <input
            id={idFim}
            className="campo-controle"
            type="date"
            value={filtros.periodoFim ?? ""}
            min={filtros.periodoInicio}
            onChange={(evento) => onChange({ periodoFim: normalizarData(evento.target.value) })}
          />
        </div>

      </div>

      <div className="filtros-acoes">
        <button
          type="button"
          className="botao-secundario"
          onClick={onLimpar}
          disabled={!algumFiltroAtivo}
        >
          Limpar filtros
        </button>
      </div>
    </div>
  );
}
