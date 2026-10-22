"""Server web di Grabby: in locale (default) o online (GRABBY_MODE=online)."""

import os
import subprocess
import sys
import threading
import time
from collections import defaultdict, deque

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from downloader import FORMATS, RESOLUTIONS, JobManager, get_info, is_supported_url
from registro import DICHIARAZIONE, DICHIARAZIONE_VERSIONE, DownloadLog, computer_user

ONLINE = os.environ.get("GRABBY_MODE", "local").lower() == "online"
# Lingue della pagina: devono coincidere con LANGUAGES in static/i18n.js.
LANGUAGES = ("it", "en", "es", "fr", "de", "pt")
# Online i file restano sul server solo finché l'utente li scarica.
FILE_MAX_AGE = 3600
DOWNLOADS_PER_HOUR = int(os.environ.get("GRABBY_LIMITE_ORARIO", "10"))
MAX_ACTIVE_PER_IP = 2
INFO_PER_HOUR = 60

app = Flask(__name__, static_folder="static")
# Dietro un proxy (es. Caddy) l'IP vero arriva in X-Forwarded-For: ci si fida
# solo del numero di proxy dichiarato, altrimenti chiunque potrebbe falsificarlo.
TRUSTED_PROXIES = int(os.environ.get("GRABBY_PROXY_FIDATI", "0"))
if TRUSTED_PROXIES:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=TRUSTED_PROXIES, x_proto=TRUSTED_PROXIES, x_host=TRUSTED_PROXIES)

# GDPR: online il registro si tiene per poco tempo (legittimo interesse).
retention = os.environ.get("GRABBY_CONSERVAZIONE_GIORNI", "30" if ONLINE else "")
jobs = JobManager(log=DownloadLog(retention_days=int(retention) if retention else None))
# Nel container (vedi Dockerfile) o online non c'è un Finder da aprire.
CAN_OPEN_FOLDER = os.environ.get("GRABBY_IN_CONTAINER") != "1" and not ONLINE


class RateLimiter:
    """Limite di richieste per IP in una finestra di tempo (in memoria)."""

    def __init__(self, limit: int, window: float = 3600):
        self.limit = limit
        self.window = window
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True


download_limiter = RateLimiter(DOWNLOADS_PER_HOUR)
info_limiter = RateLimiter(INFO_PER_HOUR)


def _json_body() -> dict:
    return request.get_json(silent=True) or {}


def _error(code: str, message: str, status: int, detail: str = ""):
    """Errore per la pagina: `code` permette di tradurre il messaggio nel browser."""
    data = {"error": message, "code": code}
    if detail:
        data["detail"] = detail
    return jsonify(data), status


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


def _page_language() -> str:
    """Lingua chiesta con ?lang=xx, altrimenti quella del browser; italiano se non c'è."""
    lang = request.args.get("lang", "")
    if lang in LANGUAGES:
        return lang
    return request.accept_languages.best_match(LANGUAGES, default="it")


@app.get("/note-legali")
def legal_notes():
    # Le traduzioni sono di cortesia: fa fede il testo italiano.
    lang = _page_language()
    name = "note-legali.html" if lang == "it" else f"note-legali.{lang}.html"
    return send_from_directory(app.static_folder, name)


@app.get("/privacy")
def privacy():
    return send_from_directory(app.static_folder, "privacy.html")


@app.get("/api/options")
def options():
    return jsonify(
        formats=[{"value": k, "label": v["label"], "audio_only": v["audio_only"]} for k, v in FORMATS.items()],
        resolutions=RESOLUTIONS,
        # Nel container la cartella vera è sul Mac: compose.yaml la passa come etichetta.
        download_dir=None if ONLINE else os.environ.get("DOWNLOAD_DIR_LABEL") or str(jobs.output_dir),
        can_open_folder=CAN_OPEN_FOLDER,
        online=ONLINE,
        declaration=DICHIARAZIONE,
    )


@app.post("/api/info")
def info():
    url = (_json_body().get("url") or "").strip()
    if not is_supported_url(url):
        return _error("invalid_url", "Inserisci un link valido di YouTube o Facebook.", 400)
    if ONLINE and not info_limiter.allow(request.remote_addr):
        return _error("too_many", "Troppe richieste: riprova tra un po'.", 429)
    try:
        return jsonify(get_info(url))
    except Exception as exc:  # noqa: BLE001
        return _error("info_failed", f"Impossibile leggere il video: {exc}", 400, detail=str(exc))


@app.post("/api/download")
def download():
    body = _json_body()
    url = (body.get("url") or "").strip()
    fmt = body.get("format", "mp4")
    resolution = str(body.get("resolution", "best"))
    user_name = " ".join(str(body.get("name") or "").split())[:80]
    ip = request.remote_addr
    if not is_supported_url(url):
        return _error("invalid_url", "Inserisci un link valido di YouTube o Facebook.", 400)
    if not user_name:
        return _error("name_required", "Scrivi il tuo nome prima di scaricare.", 400)
    if body.get("accepted") is not True:
        return _error("not_accepted", "Per scaricare devi accettare l'avviso di responsabilità.", 400)
    if ONLINE:
        jobs.sweep(FILE_MAX_AGE, delete_files=True)
        if jobs.active_count(ip) >= MAX_ACTIVE_PER_IP:
            return _error("busy", "Hai già dei download in corso: aspetta che finiscano.", 429)
        if not download_limiter.allow(ip):
            return _error("rate_limited", "Hai raggiunto il limite di download per quest'ora.", 429)
    try:
        job = jobs.start(url, fmt, resolution, requested_by={
            "nome": user_name,
            "utente_computer": "" if ONLINE else computer_user(),
            "ip": ip,
            "browser": request.headers.get("User-Agent", "")[:300],
            "lingua": _log_language(body.get("lang"), request.headers.get("Accept-Language", "")[:100]),
            "dichiarazione": f"accettata {DICHIARAZIONE_VERSIONE}",
        })
    except ValueError as exc:
        return _error("invalid_option", str(exc), 400)
    return jsonify(_public(job.to_dict())), 202


def _log_language(page_lang, browser_lang: str) -> str:
    """Nel registro: lingua scelta nella pagina e, tra parentesi, quella del browser."""
    if page_lang in LANGUAGES and page_lang != browser_lang:
        return f"{page_lang} (browser: {browser_lang})" if browser_lang else page_lang
    return browser_lang


def _public(data: dict) -> dict:
    # Online il percorso sul server non riguarda l'utente.
    if ONLINE:
        data.pop("filepath", None)
    return data


@app.get("/api/progress/<job_id>")
def progress(job_id):
    job = jobs.get(job_id)
    if job is None:
        return _error("not_found", "Download non trovato.", 404)
    return jsonify(_public(job.to_dict()))


@app.get("/api/file/<job_id>")
def file(job_id):
    """Online: consegna il file al browser e lo cancella dal server."""
    job = jobs.get(job_id)
    if not ONLINE or job is None or job.status != "completato" or not job.filepath:
        return jsonify(error="File non disponibile."), 404
    # Solo chi ha chiesto il download può ritirarlo.
    if job.requested_by.get("ip") != request.remote_addr:
        return jsonify(error="File non disponibile."), 404
    path = job.filepath
    if not os.path.exists(path):
        return jsonify(error="File non disponibile."), 404
    jobs.forget(job_id)
    # Apre il file e lo cancella subito: su Linux il contenuto resta leggibile
    # finché la risposta non è finita, poi sparisce dal server.
    handle = open(path, "rb")
    os.remove(path)
    return send_file(handle, as_attachment=True, download_name=os.path.basename(path))


@app.post("/api/open-folder")
def open_folder():
    """Apre la cartella dei download nel Finder (o equivalente)."""
    if not CAN_OPEN_FOLDER:
        return jsonify(ok=False, error="Qui non posso aprire la cartella."), 200
    path = str(jobs.output_dir)
    if sys.platform == "darwin":
        subprocess.Popen(["open", path])
    elif sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", path])
    return jsonify(ok=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"\n  Grabby Video Downloader avviato ({'online' if ONLINE else 'locale'}): http://127.0.0.1:{port}\n")
    print(f"  I file verranno salvati in: {jobs.output_dir}")
    print(f"  Registro dei download: {jobs.log.path}\n")
    # Solo in locale: non esposto alla rete. Nel container HOST=0.0.0.0, ma
    # compose.yaml pubblica la porta solo su 127.0.0.1 del Mac.
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=port, debug=False, threaded=True)
