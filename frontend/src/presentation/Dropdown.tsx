import { useId } from "react";

export interface DropdownOption {
  value: string;
  label: string;
}

export interface DropdownProps {
  /** Rótulo do filtro, ex.: "Concessionária". */
  label: string;
  options: DropdownOption[];
  /** Valor selecionado; `undefined` ou "" significa "sem filtro". */
  value?: string;
  /** Recebe `undefined` quando o usuário volta para a opção "Todos". */
  onChange: (value: string | undefined) => void;
  /** Texto da opção neutra. */
  placeholder?: string;
  disabled?: boolean;
}

/**
 * Select de seleção única usado por todos os filtros da barra.
 *
 * Usa o `<select>` nativo de propósito: acessibilidade de teclado, leitores
 * de tela e comportamento em mobile já vêm prontos, sem dependência externa.
 * A opção neutra ("Todos") tem valor vazio e é traduzida para `undefined`,
 * que é como `VinShareFiltros` representa um filtro não aplicado.
 */
export default function Dropdown({
  label,
  options,
  value,
  onChange,
  placeholder = "Todos",
  disabled = false
}: DropdownProps) {
  const id = useId();

  return (
    <div className="campo">
      <label className="campo-label" htmlFor={id}>
        {label}
      </label>
      <select
        id={id}
        className="campo-controle"
        value={value ?? ""}
        disabled={disabled}
        onChange={(evento) => onChange(evento.target.value === "" ? undefined : evento.target.value)}
      >
        <option value="">{placeholder}</option>
        {options.map((opcao) => (
          <option key={opcao.value} value={opcao.value}>
            {opcao.label}
          </option>
        ))}
      </select>
    </div>
  );
}
