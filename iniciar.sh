#!/usr/bin/env bash
# Inicia o CV Match (backend + frontend) e abre o navegador.
# Na primeira execução, cria o ambiente Python e instala as dependências.
# Para encerrar, pressione Ctrl+C.

set -euo pipefail
RAIZ="$(cd "$(dirname "$0")" && pwd)"

# --- Backend: ambiente virtual e dependências (só na primeira vez) ---
if [ ! -d "$RAIZ/backend/.venv" ]; then
  echo "Criando o ambiente Python (só na primeira vez)..."
  python3 -m venv "$RAIZ/backend/.venv"
  "$RAIZ/backend/.venv/bin/pip" install -q --upgrade pip
  "$RAIZ/backend/.venv/bin/pip" install -q -r "$RAIZ/backend/requirements.txt"
  echo "Pronto. Para a análise semântica completa, rode depois:"
  echo "  $RAIZ/backend/.venv/bin/pip install -r $RAIZ/backend/requirements-semantic.txt"
fi

# --- Frontend: dependências (só na primeira vez) ---
if [ ! -d "$RAIZ/frontend/node_modules" ]; then
  echo "Instalando as dependências do frontend (só na primeira vez)..."
  (cd "$RAIZ/frontend" && npm install --silent)
fi

# --- Chave do Gemini (opcional) ---
# Pergunta a chave quando ela ainda não está no .env (ou com ./iniciar.sh --chave,
# para trocá-la). Enter sem digitar nada segue no modo local, sem IA generativa.
ENV_ARQ="$RAIZ/.env"
chave_atual() {
  [ -f "$ENV_ARQ" ] || return 0
  sed -n 's/^[[:space:]]*GEMINI_API_KEY[[:space:]]*=[[:space:]]*//p' "$ENV_ARQ" | tail -n 1 | tr -d "\"' \r"
}
salvar_chave() {
  [ -f "$ENV_ARQ" ] || cp "$RAIZ/.env.example" "$ENV_ARQ"
  local tmp
  tmp="$(mktemp)"
  NOVA_CHAVE="$1" awk '
    /^[[:space:]]*GEMINI_API_KEY[[:space:]]*=/ { if (!feito) print "GEMINI_API_KEY=" ENVIRON["NOVA_CHAVE"]; feito = 1; next }
    { print }
    END { if (!feito) print "GEMINI_API_KEY=" ENVIRON["NOVA_CHAVE"] }
  ' "$ENV_ARQ" > "$tmp"
  cat "$tmp" > "$ENV_ARQ" && rm -f "$tmp"
  chmod 600 "$ENV_ARQ"
}
if [ -t 0 ] && [ -z "${GEMINI_API_KEY:-}" ] && { [ "${1:-}" = "--chave" ] || [ -z "$(chave_atual)" ]; }; then
  echo
  echo "Chave do Gemini (opcional): ativa as sugestões e a reescrita com IA."
  echo "Gere uma gratuita em https://aistudio.google.com/apikey"
  printf "Cole a chave e tecle Enter (ou só Enter para usar o modo local): "
  read -r -s CHAVE || CHAVE=""
  echo
  CHAVE="$(printf '%s' "$CHAVE" | tr -d "\"' \r\t")"
  if [ -n "$CHAVE" ]; then
    salvar_chave "$CHAVE"
    echo "Chave salva em $ENV_ARQ (para trocar: ./iniciar.sh --chave)."
  else
    echo "Seguindo no modo local, sem IA generativa."
  fi
fi

# Encerra os dois servidores ao sair (Ctrl+C ou erro).
encerrar() {
  echo
  echo "Encerrando o CV Match..."
  kill "$PID_BACKEND" "$PID_FRONTEND" 2>/dev/null || true
}
trap encerrar EXIT INT TERM

(cd "$RAIZ/backend" && exec .venv/bin/uvicorn app.main:app --port 8000 --log-level warning) &
PID_BACKEND=$!
(cd "$RAIZ/frontend" && exec node_modules/.bin/vite --port 5173 --strictPort --logLevel warn) &
PID_FRONTEND=$!

# Espera o backend responder antes de abrir o navegador.
for _ in $(seq 1 60); do
  if curl -s http://localhost:5173/api/health >/dev/null 2>&1; then break; fi
  sleep 1
done

echo
echo "CV Match rodando em http://localhost:5173  (Ctrl+C para encerrar)"
[ -n "${SEM_NAVEGADOR:-}" ] || open http://localhost:5173 2>/dev/null || true
wait
