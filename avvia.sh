#!/usr/bin/env bash
# Avvia Video Downloader: crea l'ambiente Python al primo avvio,
# aggiorna yt-dlp e apre la pagina nel browser.
set -e
cd "$(dirname "$0")"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg non trovato. Installalo con:  brew install ffmpeg"
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Primo avvio: creo l'ambiente Python..."
  python3 -m venv .venv
fi

./.venv/bin/pip install -q --upgrade pip
# yt-dlp va aggiornato spesso: YouTube e Facebook cambiano di frequente.
./.venv/bin/pip install -q --upgrade -r requirements.txt

PORT="${PORT:-8000}"
export PORT
( sleep 2 && open "http://127.0.0.1:${PORT}" >/dev/null 2>&1 || true ) &
exec ./.venv/bin/python app.py
