import { useCallback, useState } from "react";
import type { CredenciaisLogin, Sessao } from "../domain/types";
import { ApiError, toApiError } from "../infrastructure/apiClient";
import { login } from "../infrastructure/dataSource";

export interface EstadoLogin {
  loading: boolean;
  error: ApiError | null;
  /** `true` em sucesso, `false` em falha — o formulário decide o que fazer sem try/catch. */
  entrar: (credenciais: CredenciaisLogin) => Promise<boolean>;
}

/**
 * Autentica e devolve a sessão via `aoAutenticar` (quem persiste — `App.tsx` —
 * decide onde/como guardar, este hook só faz a chamada e trata o estado de
 * loading/erro, mesmo padrão dos demais hooks de `application/`).
 */
export function useLogin(aoAutenticar: (sessao: Sessao) => void): EstadoLogin {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const entrar = useCallback(
    async (credenciais: CredenciaisLogin) => {
      setLoading(true);
      setError(null);

      try {
        const sessao = await login(credenciais);
        aoAutenticar(sessao);
        return true;
      } catch (erro) {
        setError(toApiError(erro));
        return false;
      } finally {
        setLoading(false);
      }
    },
    [aoAutenticar]
  );

  return { loading, error, entrar };
}
