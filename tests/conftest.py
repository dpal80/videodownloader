import os
import tempfile
from pathlib import Path

import pytest

# Il registro dei test non deve finire nei Documenti di chi li esegue.
os.environ.setdefault("GRABBY_REGISTRO_DIR", tempfile.mkdtemp(prefix="grabby-test-registro-"))

import downloader  # noqa: E402


class FakeYDL:
    """Sostituto di yt_dlp.YoutubeDL: "scarica" un piccolo file senza rete."""

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def extract_info(self, url, download):
        for hook in self.opts["progress_hooks"]:
            hook({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100})
            hook({"status": "finished"})
        out = Path(self.opts["outtmpl"]).parent / "video [x].mp4"
        out.write_bytes(b"data")
        return {"title": "Video di prova", "requested_downloads": [{"filepath": str(out)}]}


@pytest.fixture
def fake_ydl(monkeypatch):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FakeYDL)
