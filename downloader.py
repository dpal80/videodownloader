"""Logica di download basata su yt-dlp (indipendente da Flask)."""

import os
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

ALLOWED_HOSTS = (
    "youtube.com",
    "youtu.be",
    "youtube-nocookie.com",
    "facebook.com",
    "fb.watch",
    "fb.com",
)

FORMATS = {
    "mp4": {"label": "MP4 (video)", "audio_only": False},
    "webm": {"label": "WebM (video)", "audio_only": False},
    "mp3": {"label": "MP3 (solo audio)", "audio_only": True},
    "m4a": {"label": "M4A (solo audio)", "audio_only": True},
}

RESOLUTIONS = ["best", "2160", "1440", "1080", "720", "480", "360", "240", "144"]


def default_download_dir() -> Path:
    return Path(os.environ.get("DOWNLOAD_DIR", Path.home() / "Downloads")).expanduser()


def is_supported_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS)


def build_format_selector(fmt: str, resolution: str) -> str:
    """Restituisce la stringa di selezione formato per yt-dlp."""
    if FORMATS[fmt]["audio_only"]:
        if fmt == "m4a":
            return "bestaudio[ext=m4a]/bestaudio/best"
        return "bestaudio/best"

    h = "" if resolution == "best" else f"[height<={int(resolution)}]"
    if fmt == "mp4":
        # Preferisce H.264 + AAC (compatibili con QuickTime), poi qualsiasi codec.
        return (
            f"bestvideo{h}[vcodec^=avc1]+bestaudio[ext=m4a]/"
            f"bestvideo{h}+bestaudio/best{h}/best"
        )
    # webm: preferisce VP9/AV1 + Opus
    return (
        f"bestvideo{h}[ext=webm]+bestaudio[ext=webm]/"
        f"bestvideo{h}+bestaudio/best{h}/best"
    )


def build_ydl_options(fmt: str, resolution: str, output_dir: Path) -> dict:
    if fmt not in FORMATS:
        raise ValueError(f"Formato non supportato: {fmt}")
    if resolution not in RESOLUTIONS:
        raise ValueError(f"Risoluzione non supportata: {resolution}")

    opts = {
        "format": build_format_selector(fmt, resolution),
        "outtmpl": str(output_dir / "%(title).150B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    if FORMATS[fmt]["audio_only"]:
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": fmt,
                "preferredquality": "192",
            }
        ]
    else:
        # Unisce nel formato scelto; se i codec non sono compatibili usa MKV
        # e poi lo converte nel formato richiesto.
        opts["merge_output_format"] = f"{fmt}/mkv"
        opts["postprocessors"] = [
            {"key": "FFmpegVideoConvertor", "preferedformat": fmt}
        ]
    return opts


def get_info(url: str) -> dict:
    """Legge titolo, miniatura, durata e risoluzioni disponibili senza scaricare."""
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    if info.get("_type") == "playlist" and info.get("entries"):
        info = next(e for e in info["entries"] if e)

    heights = sorted(
        {f["height"] for f in info.get("formats") or [] if f.get("height") and f.get("vcodec") != "none"},
        reverse=True,
    )
    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader"),
        "heights": heights,
    }


class Job:
    def __init__(self, url: str, fmt: str, resolution: str, requested_by: dict | None = None):
        self.id = uuid.uuid4().hex
        # Chi ha chiesto il download (utente, IP, browser...): va nel registro.
        self.requested_by = requested_by or {}
        self.title = None
        self.url = url
        self.fmt = fmt
        self.resolution = resolution
        self.status = "in coda"  # in coda | download | conversione | completato | errore
        self.percent = 0.0
        self.speed = None
        self.eta = None
        self.filepath = None
        self.error = None
        self.finished_at = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "percent": round(self.percent, 1),
            "speed": self.speed,
            "eta": self.eta,
            "filename": Path(self.filepath).name if self.filepath else None,
            "filepath": self.filepath,
            "error": self.error,
        }


class JobManager:
    def __init__(self, output_dir: Path | None = None, log=None):
        self.output_dir = output_dir or default_download_dir()
        self.log = log  # registro.DownloadLog, se presente
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def forget(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)

    def active_count(self, ip: str) -> int:
        """Download ancora in corso chiesti da questo indirizzo IP."""
        with self._lock:
            return sum(
                1 for j in self._jobs.values()
                if j.finished_at is None and j.requested_by.get("ip") == ip
            )

    def sweep(self, max_age_seconds: float, delete_files: bool = False) -> None:
        """Dimentica i download finiti da più di max_age_seconds.

        Online i file restano sul server solo finché l'utente li scarica:
        con delete_files=True vengono cancellati anche quelli mai ritirati."""
        now = time.time()
        with self._lock:
            old = [j for j in self._jobs.values() if j.finished_at and now - j.finished_at > max_age_seconds]
            for j in old:
                del self._jobs[j.id]
        if delete_files:
            for j in old:
                if j.filepath:
                    Path(j.filepath).unlink(missing_ok=True)

    def start(self, url: str, fmt: str, resolution: str, requested_by: dict | None = None) -> Job:
        build_ydl_options(fmt, resolution, self.output_dir)  # valida i parametri
        job = Job(url, fmt, resolution, requested_by)
        with self._lock:
            self._jobs[job.id] = job
        self._log(job, "richiesto")
        threading.Thread(target=self._run, args=(job,), daemon=True).start()
        return job

    def _run(self, job: Job) -> None:
        def progress_hook(d):
            if d["status"] == "downloading":
                job.status = "download"
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total:
                    job.percent = min(100.0, d.get("downloaded_bytes", 0) * 100 / total)
                job.speed = d.get("speed")
                job.eta = d.get("eta")
            elif d["status"] == "finished":
                job.percent = 100.0

        def postprocessor_hook(d):
            if d["status"] == "started":
                job.status = "conversione"

        tmp_dir = None
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            # Scarica in una cartella temporanea: i file intermedi (e quelli
            # cancellati dalle conversioni) non toccano mai la cartella finale.
            tmp_dir = Path(tempfile.mkdtemp(prefix=".videodownloader-", dir=self.output_dir))
            opts = build_ydl_options(job.fmt, job.resolution, tmp_dir)
            opts.update(progress_hooks=[progress_hook], postprocessor_hooks=[postprocessor_hook])
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(job.url, download=True)
            job.title = info.get("title")
            downloads = info.get("requested_downloads") or []
            produced = Path(downloads[-1]["filepath"]) if downloads else None
            if produced is None or not produced.exists():
                raise RuntimeError("Il download non ha prodotto alcun file.")
            final = _unique_path(self.output_dir / produced.name)
            shutil.move(str(produced), final)
            job.filepath = str(final)
            job.percent = 100.0
            job.status = "completato"
        except Exception as exc:  # noqa: BLE001 - mostriamo l'errore all'utente
            job.status = "errore"
            job.error = str(exc).replace("\x1b[0;31mERROR:\x1b[0m ", "").replace("ERROR: ", "").strip()
        finally:
            if tmp_dir is not None:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            job.finished_at = time.time()
            self._log(job, job.status)

    def log_event(self, event: str, url: str, fmt: str, resolution: str, requested_by: dict) -> None:
        """Annota nel registro una richiesta che non diventa un download (es. link bloccato)."""
        job = Job(url, fmt, resolution, requested_by)
        job.status = event
        self._log(job, event)

    def _log(self, job: Job, event: str) -> None:
        if self.log is None:
            return
        try:
            self.log.record({
                **job.requested_by,
                "evento": event,
                "link": job.url,
                "titolo": job.title,
                "formato": job.fmt,
                "risoluzione": job.resolution,
                "esito": job.status,
                "file": Path(job.filepath).name if job.filepath else "",
                "errore": job.error,
            })
        except OSError:
            pass  # il registro non deve mai bloccare un download


def _unique_path(path: Path) -> Path:
    """Se il file esiste già aggiunge (1), (2), ... invece di sovrascriverlo."""
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1
