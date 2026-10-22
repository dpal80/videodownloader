#!/usr/bin/env bash
# Avvia Grabby Video Downloader: crea l'ambiente Python al primo avvio,
# aggiorna yt-dlp e apre la pagina nel browser.
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
export PORT
# Avviato dal Finder il PATH è minimo: aggiunge le cartelle di Homebrew e uv.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

# Se Grabby è già acceso, apre solo la pagina.
if curl -fs -o /dev/null "http://127.0.0.1:${PORT}/api/options"; then
  open "http://127.0.0.1:${PORT}"
  exit 0
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg non trovato. Installalo con:  brew install ffmpeg"
  exit 1
fi

# uv (https://docs.astral.sh/uv/) se presente: installa da solo Python 3.12
# senza bisogno di Homebrew o della password di amministratore.
UV="$(command -v uv || true)"
[ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ] && UV="$HOME/.local/bin/uv"

if [ -n "$UV" ]; then
  if [ ! -x .venv/bin/python ]; then
    echo "Primo avvio: creo l'ambiente Python con uv..."
    "$UV" venv --python 3.12 .venv
  fi
  # yt-dlp va aggiornato spesso: YouTube e Facebook cambiano di frequente.
  "$UV" pip install -q --python .venv/bin/python --upgrade -r requirements.txt
else
  if [ ! -x .venv/bin/python ]; then
    if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
      echo "Serve Python 3.10 o più recente (trovato: $(python3 --version 2>&1))."
      echo "Il modo più semplice è installare uv e rilanciare questo script:"
      echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
      exit 1
    fi
    echo "Primo avvio: creo l'ambiente Python..."
    python3 -m venv .venv
  fi
  ./.venv/bin/python -m pip install -q --upgrade pip
  ./.venv/bin/python -m pip install -q --upgrade -r requirements.txt
fi

( sleep 2 && open "http://127.0.0.1:${PORT}" >/dev/null 2>&1 || true ) &
exec ./.venv/bin/python app.py
