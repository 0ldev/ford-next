import { useCallback, useState } from "react";
import type { Sessao } from "../domain/types";
import { limparSessao, obterSessao, salvarSessao, sessaoValida } from "../infrastructure/session";
import DashboardPage from "./DashboardPage";
import LoginPage from "./LoginPage";
import "./styles.css";

const ROTULO_PERFIL: Record<Sessao["perfil"], string> = {
  gestor: "Gestor",
  concessionaria: "Concessionária"
};

/**
 * Porta de entrada do app: sem sessão válida, mostra `LoginPage`; com sessão,
 * o dashboard — mais uma barra fina com quem está logado e "Sair".
 *
 * Verifica a expiração só no carregamento da página (não há interceptor
 * global de 401 em cada chamada): se o token expirar no meio do uso, a
 * próxima requisição volta como erro comum na seção — recarregar a página
 * já resolve, mas não há logout automático "no ato". Suficiente para o
 * escopo atual; um interceptor global fica para uma iteração futura.
 */
export default function App() {
  const [sessao, setSessao] = useState<Sessao | null>(() => {
    const guardada = obterSessao();
    return sessaoValida(guardada) ? guardada : null;
  });

  const aoAutenticar = useCallback((nova: Sessao) => {
    salvarSessao(nova);
    setSessao(nova);
  }, []);

  const sair = useCallback(() => {
    limparSessao();
    setSessao(null);
  }, []);

  if (!sessao) {
    return <LoginPage onAutenticado={aoAutenticar} />;
  }

  return (
    <div>
      <div className="sessao-barra">
        <span>
          {ROTULO_PERFIL[sessao.perfil]}
          {sessao.dealerCode ? ` ${sessao.dealerCode}` : ""}
        </span>
        <button type="button" className="botao-link" onClick={sair}>
          Sair
        </button>
      </div>
      <DashboardPage perfil={sessao.perfil} dealerCode={sessao.dealerCode} />
    </div>
  );
}
