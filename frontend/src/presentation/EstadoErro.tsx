export interface EstadoErroProps {
  /** Mensagem já pronta para exibição, normalmente `ApiError.message`. */
  mensagem: string;
  /** Sem callback, o bloco mostra só a mensagem — usado onde não há o que repetir. */
  onTentarNovamente?: () => void;
}

/**
 * Bloco de erro padrão do dashboard.
 *
 * Existe para que as cinco seções que consomem hooks relatem falha do mesmo
 * jeito: um `role="alert"`, a mensagem e a mesma nova tentativa. Antes cada
 * seção tinha o seu próprio markup, e uma delas nem classe tinha.
 *
 * A caixa ao redor (altura do gráfico, moldura do painel) continua sendo
 * responsabilidade de quem chama, porque isso é layout da seção, não do erro.
 */
export default function EstadoErro({ mensagem, onTentarNovamente }: EstadoErroProps) {
  return (
    <div className="estado-erro" role="alert">
      <p className="estado-erro-mensagem">{mensagem}</p>
      {onTentarNovamente && (
        <button type="button" className="botao-secundario" onClick={onTentarNovamente}>
          Tentar novamente
        </button>
      )}
    </div>
  );
}
