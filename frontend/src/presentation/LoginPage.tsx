import { useId, useState, type FormEvent } from "react";
import { useLogin } from "../application/useLogin";
import type { Sessao } from "../domain/types";
import EstadoErro from "./EstadoErro";

export interface LoginPageProps {
  onAutenticado: (sessao: Sessao) => void;
}

/**
 * Tela de login — única porta de entrada do dashboard (`App.tsx` renderiza
 * isto no lugar do `DashboardPage` enquanto não há sessão válida).
 */
export default function LoginPage({ onAutenticado }: LoginPageProps) {
  const idUsuario = useId();
  const idSenha = useId();
  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const { loading, error, entrar } = useLogin(onAutenticado);

  const aoSubmeter = (evento: FormEvent) => {
    evento.preventDefault();
    void entrar({ usuario, senha });
  };

  return (
    <div className="login-pagina">
      <form className="login-cartao" onSubmit={aoSubmeter}>
        <div className="marca login-marca">
          <span className="marca-selo" aria-hidden="true">
            Ford
          </span>
          <div>
            <h1 className="cabecalho-titulo">VIN Share Intelligence Hub</h1>
            <p className="cabecalho-subtitulo">Entre para acompanhar a retenção da rede.</p>
          </div>
        </div>

        <div className="campo">
          <label className="campo-label" htmlFor={idUsuario}>
            Usuário
          </label>
          <input
            id={idUsuario}
            className="campo-controle"
            type="text"
            autoComplete="username"
            value={usuario}
            onChange={(evento) => setUsuario(evento.target.value)}
            required
          />
        </div>

        <div className="campo">
          <label className="campo-label" htmlFor={idSenha}>
            Senha
          </label>
          <input
            id={idSenha}
            className="campo-controle"
            type="password"
            autoComplete="current-password"
            value={senha}
            onChange={(evento) => setSenha(evento.target.value)}
            required
          />
        </div>

        {error && <EstadoErro mensagem={error.message} />}

        <button type="submit" className="botao-primario login-botao" disabled={loading}>
          {loading ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
