import type { Sessao } from "../domain/types";

const CHAVE_SESSAO = "ford-next:sessao";

/**
 * Persistência da sessão (token JWT + perfil) em `localStorage`.
 *
 * Tudo aqui é best-effort: `localStorage` pode não existir (modo privado,
 * storage bloqueado) — nesse caso a sessão simplesmente não sobrevive a um
 * reload, em vez de quebrar a página.
 */
export function salvarSessao(sessao: Sessao): void {
  try {
    localStorage.setItem(CHAVE_SESSAO, JSON.stringify(sessao));
  } catch {
    // sem storage disponível: a sessão só dura a aba atual, em memória do React.
  }
}

export function obterSessao(): Sessao | null {
  try {
    const bruto = localStorage.getItem(CHAVE_SESSAO);
    return bruto ? (JSON.parse(bruto) as Sessao) : null;
  } catch {
    return null;
  }
}

export function limparSessao(): void {
  try {
    localStorage.removeItem(CHAVE_SESSAO);
  } catch {
    // nada a limpar se não há storage
  }
}

/** `false` também para `sessao` nula/indefinida — simplifica quem só quer saber "posso usar isso?". */
export function sessaoValida(sessao: Sessao | null | undefined): sessao is Sessao {
  if (!sessao) return false;
  return new Date(sessao.expiraEm).getTime() > Date.now();
}
