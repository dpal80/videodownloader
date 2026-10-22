"""Registro dei download: un file CSV (apribile con Excel) con chi ha scaricato
cosa e la conferma di responsabilità. Resta sul computer (o sul server) dove
gira Grabby."""

import csv
import getpass
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Avviso che l'utente accetta prima di scaricare: la versione finisce nel registro,
# così si sa a quale dichiarazione si riferisce ogni riga.
DICHIARAZIONE_VERSIONE = "v2"
DICHIARAZIONE = (
    "L'utilizzo dei video e degli audio scaricati è permesso solo nei casi "
    "consentiti (in verde) nelle note legali: video tuoi, con licenza libera "
    "(Creative Commons, pubblico dominio) o con il permesso dell'autore. "
    "Continuando e scaricando il video ti assumi la piena responsabilità legale "
    "del suo utilizzo."
)

COLUMNS = [
    "data_ora",
    "evento",
    "utente_computer",
    "nome",
    "ip",
    "browser",
    "lingua",
    "dichiarazione",
    "link",
    "titolo",
    "formato",
    "risoluzione",
    "esito",
    "file",
    "errore",
]


def default_log_path() -> Path:
    folder = os.environ.get("GRABBY_REGISTRO_DIR", Path.home() / "Documents" / "Grabby")
    return Path(folder).expanduser() / "registro-download.csv"


def computer_user() -> str:
    # Nel container l'utente è "root": compose.yaml passa quello del Mac.
    try:
        return os.environ.get("GRABBY_UTENTE_COMPUTER") or getpass.getuser()
    except Exception:  # noqa: BLE001
        return "sconosciuto"


def _safe(value) -> str:
    """Evita che Excel interpreti un campo come formula (=, +, -, @)."""
    text = "" if value is None else str(value).replace("\r", " ").replace("\n", " ")
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def _now() -> datetime:
    # Con il fuso orario (es. +02:00): l'ora resta chiara anche nel container.
    return datetime.now().astimezone()


def _parse_date(value) -> datetime:
    try:
        date = datetime.fromisoformat(str(value))
    except ValueError:
        return datetime.max.replace(tzinfo=timezone.utc)  # riga illeggibile: meglio tenerla
    return date if date.tzinfo else date.astimezone()


class DownloadLog:
    def __init__(self, path: Path | None = None, retention_days: int | None = None):
        self.path = path or default_log_path()
        # GDPR: le righe più vecchie della conservazione vengono cancellate.
        self.retention_days = retention_days
        self._lock = threading.Lock()
        self._last_purge = None

    def purge(self, now: datetime | None = None) -> int:
        """Cancella le righe più vecchie di retention_days. Restituisce quante."""
        if not self.retention_days or not self.path.exists():
            return 0
        now = now or _now()
        limit = now - timedelta(days=self.retention_days)
        with self._lock:
            with open(self.path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f, delimiter=";"))
            keep = [r for r in rows if _parse_date(r.get("data_ora")) >= limit]
            if len(keep) != len(rows):
                with open(self.path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";", extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(keep)
            self._last_purge = now
        return len(rows) - len(keep)

    def record(self, row: dict) -> None:
        now = _now()
        if self.retention_days and (self._last_purge is None or now - self._last_purge > timedelta(days=1)):
            self.purge(now)
        row = {"data_ora": now.isoformat(timespec="seconds"), **row}
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            new_file = not self.path.exists() or self.path.stat().st_size == 0
            # utf-8-sig: Excel riconosce le lettere accentate.
            with open(self.path, "a", newline="", encoding="utf-8-sig" if new_file else "utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";")
                if new_file:
                    writer.writeheader()
                writer.writerow({c: _safe(row.get(c)) for c in COLUMNS})
