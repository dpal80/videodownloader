"""Server web locale per scaricare video da YouTube e Facebook."""

import os
import subprocess
import sys

from flask import Flask, jsonify, request, send_from_directory

from downloader import FORMATS, RESOLUTIONS, JobManager, get_info, is_supported_url

app = Flask(__name__, static_folder="static")
jobs = JobManager()
# Nel container (vedi Dockerfile) non c'è un Finder da aprire.
CAN_OPEN_FOLDER = os.environ.get("GRABBY_IN_CONTAINER") != "1"


def _json_body() -> dict:
    return request.get_json(silent=True) or {}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/note-legali")
def legal_notes():
    return send_from_directory(app.static_folder, "note-legali.html")


@app.get("/api/options")
def options():
    return jsonify(
        formats=[{"value": k, "label": v["label"], "audio_only": v["audio_only"]} for k, v in FORMATS.items()],
        resolutions=RESOLUTIONS,
        # Nel container la cartella vera è sul Mac: compose.yaml la passa come etichetta.
        download_dir=os.environ.get("DOWNLOAD_DIR_LABEL") or str(jobs.output_dir),
        can_open_folder=CAN_OPEN_FOLDER,
    )


@app.post("/api/info")
def info():
    url = (_json_body().get("url") or "").strip()
    if not is_supported_url(url):
        return jsonify(error="Inserisci un link valido di YouTube o Facebook."), 400
    try:
        return jsonify(get_info(url))
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=f"Impossibile leggere il video: {exc}"), 400


@app.post("/api/download")
def download():
    body = _json_body()
    url = (body.get("url") or "").strip()
    fmt = body.get("format", "mp4")
    resolution = str(body.get("resolution", "best"))
    if not is_supported_url(url):
        return jsonify(error="Inserisci un link valido di YouTube o Facebook."), 400
    try:
        job = jobs.start(url, fmt, resolution)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(job.to_dict()), 202


@app.get("/api/progress/<job_id>")
def progress(job_id):
    job = jobs.get(job_id)
    if job is None:
        return jsonify(error="Download non trovato."), 404
    return jsonify(job.to_dict())


@app.post("/api/open-folder")
def open_folder():
    """Apre la cartella dei download nel Finder (o equivalente)."""
    if not CAN_OPEN_FOLDER:
        return jsonify(ok=False, error="Nel container non posso aprire la cartella."), 200
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
    print(f"\n  Grabby Video Downloader avviato: http://127.0.0.1:{port}\n")
    print(f"  I file verranno salvati in: {jobs.output_dir}\n")
    # Solo in locale: non esposto alla rete. Nel container HOST=0.0.0.0, ma
    # compose.yaml pubblica la porta solo su 127.0.0.1 del Mac.
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=port, debug=False)
