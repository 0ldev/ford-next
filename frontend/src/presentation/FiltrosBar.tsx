import { useId } from "react";
import type { VinShareFiltros } from "../domain/types";
import {
  CONCESSIONARIAS,
  FAIXAS_IDADE,
  MODELOS,
  TIPOS_SERVICO
} from "../infrastructure/mockData";
import Dropdown, { type DropdownOption } from "./Dropdown";

export interface FiltrosBarProps {
  filtros: VinShareFiltros;
  /** Recebe apenas os campos alterados; a página faz o merge no estado. */
  onChange: (alteracao: Partial<VinShareFiltros>) => void;
  onLimpar: () => void;
}

/**
 * Opções derivadas da própria fonte de dados, para não existir uma segunda
 * lista de concessionárias/modelos divergindo do que a API devolve.
 */
const OPCOES_CONCESSIONARIA: DropdownOption[] = CONCESSIONARIAS.map((item) => ({
  value: item.dealerCode,
  label: `${item.dealerCode} — ${item.nome}`
}));

const OPCOES_MODELO: DropdownOption[] = MODELOS.map((modelo) => ({
  value: modelo,
  label: modelo
}));

const OPCOES_FAIXA_IDADE: DropdownOption[] = FAIXAS_IDADE.map((faixa) => ({
  value: faixa.value,
  label: faixa.label
}));

const OPCOES_TIPO_SERVICO: DropdownOption[] = TIPOS_SERVICO.map((tipo) => ({
  value: tipo,
  label: tipo
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
export default function FiltrosBar({ filtros, onChange, onLimpar }: FiltrosBarProps) {
  const idInicio = useId();
  const idFim = useId();

  const algumFiltroAtivo = Object.values(filtros).some(
    (valor) => valor !== undefined && valor !== ""
  );

  return (
    <div className="filtros">
      <Dropdown
        label="Concessionária"
        options={OPCOES_CONCESSIONARIA}
        value={filtros.concessionaria}
        onChange={(concessionaria) => onChange({ concessionaria })}
        placeholder="Todas"
      />

      <Dropdown
        label="Modelo"
        options={OPCOES_MODELO}
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
        options={OPCOES_TIPO_SERVICO}
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

      <div className="campo campo-acao">
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
