import { useEffect, useState } from "react";

export interface BotaoCopiarProps {
  /** Texto que vai para a área de transferência. */
  texto: string;
  /** Rótulo padrão do botão. */
  rotulo?: string;
}

/**
 * Copia um texto, com plano B para origem não segura.
 *
 * `navigator.clipboard` só existe em contexto seguro: numa demonstração
 * aberta por IP da rede local (http://192.168.x.x) ele é `undefined` e o
 * botão morreria calado. O caminho antigo com `execCommand` cobre esse caso.
 */
export async function copiarTexto(texto: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(texto);
      return true;
    }
  } catch {
    // Sem permissão: tenta o caminho legado abaixo.
  }

  try {
    const area = document.createElement("textarea");
    area.value = texto;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "0";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const copiou = document.execCommand("copy");
    document.body.removeChild(area);
    return copiou;
  } catch {
    return false;
  }
}

/**
 * Copia a mensagem pronta para a área de transferência.
 *
 * É o último passo que faltava para "insight vira ação": o consultor lê a
 * recomendação e leva o texto para o WhatsApp ou o CRM sem redigitar. O
 * retorno visual dura poucos segundos e volta ao estado inicial sozinho.
 */
export default function BotaoCopiar({ texto, rotulo = "Copiar mensagem" }: BotaoCopiarProps) {
  const [estado, setEstado] = useState<"parado" | "copiado" | "falhou">("parado");

  useEffect(() => {
    if (estado === "parado") return;
    const id = setTimeout(() => setEstado("parado"), 2400);
    return () => clearTimeout(id);
  }, [estado]);

  const aoClicar = async () => {
    setEstado((await copiarTexto(texto)) ? "copiado" : "falhou");
  };

  return (
    <button
      type="button"
      className="botao-copiar"
      onClick={aoClicar}
      data-estado={estado}
      aria-live="polite"
    >
      <span aria-hidden="true">{estado === "copiado" ? "✓" : "⧉"}</span>
      {estado === "copiado"
        ? "Copiado"
        : estado === "falhou"
          ? "Selecione o texto para copiar"
          : rotulo}
    </button>
  );
}
