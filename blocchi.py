"""Link bloccati dopo una segnalazione dei titolari dei diritti.

L'elenco è un file di testo, una voce per riga (le righe che iniziano con #
sono commenti): l'ID di un video YouTube (es. dQw4w9WgXcQ) oppure un pezzo
di indirizzo (es. facebook.com/watch/?v=123). Un link è bloccato se contiene
una delle voci. Il file si rilegge da solo quando cambia.
"""
import os
import threading
from pathlib import Path

from registro import default_log_path


def default_path() -> Path:
    return Path(os.environ.get("GRABBY_BLOCCATI", default_log_path().parent / "contenuti-bloccati.txt"))


class Blocklist:
    def __init__(self, path: Path | None = None):
        self.path = path or default_path()
        self._lock = threading.Lock()
        self._mtime = None
        self._entries: tuple[str, ...] = ()

    def entries(self) -> tuple[str, ...]:
        try:
            mtime = self.path.stat().st_mtime
        except OSError:
            return ()
        with self._lock:
            if mtime != self._mtime:
                lines = self.path.read_text(encoding="utf-8").splitlines()
                self._entries = tuple(
                    line.strip() for line in lines if line.strip() and not line.strip().startswith("#"))
                self._mtime = mtime
            return self._entries

    def is_blocked(self, url: str) -> bool:
        return any(entry in url for entry in self.entries())
