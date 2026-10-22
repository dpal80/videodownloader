from pathlib import Path

import pytest

import downloader
from app import app


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://m.youtube.com/shorts/abc",
        "https://www.facebook.com/watch/?v=123",
        "https://fb.watch/abc/",
    ],
)
def test_supported_urls(url):
    assert downloader.is_supported_url(url)


@pytest.mark.parametrize(
    "url",
    ["", "ftp://youtube.com/x", "https://evilyoutube.com/x", "https://example.com", "not a url"],
)
def test_unsupported_urls(url):
    assert not downloader.is_supported_url(url)


def test_mp4_options_limit_height():
    opts = downloader.build_ydl_options("mp4", "720", Path("/tmp/out"))
    assert "[height<=720]" in opts["format"]
    assert opts["merge_output_format"] == "mp4/mkv"
    assert opts["noplaylist"] is True
    assert opts["outtmpl"].startswith("/tmp/out/")


def test_best_resolution_has_no_height_filter():
    opts = downloader.build_ydl_options("webm", "best", Path("/tmp"))
    assert "height" not in opts["format"]
    assert opts["postprocessors"][0]["preferedformat"] == "webm"


def test_mp3_extracts_audio():
    opts = downloader.build_ydl_options("mp3", "best", Path("/tmp"))
    assert opts["format"].startswith("bestaudio")
    assert opts["postprocessors"][0]["key"] == "FFmpegExtractAudio"
    assert opts["postprocessors"][0]["preferredcodec"] == "mp3"
    assert "merge_output_format" not in opts


@pytest.mark.parametrize("fmt,res", [("avi", "best"), ("mp4", "999"), ("mp4", "abc")])
def test_invalid_options(fmt, res):
    with pytest.raises(ValueError):
        downloader.build_ydl_options(fmt, res, Path("/tmp"))


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Grabby Video Downloader" in res.data


def test_options_endpoint(client):
    data = client.get("/api/options").get_json()
    assert {f["value"] for f in data["formats"]} == {"mp4", "webm", "mp3", "m4a"}
    assert "1080" in data["resolutions"]


def test_download_rejects_bad_url(client):
    res = client.post("/api/download", json={"url": "https://example.com/v"})
    assert res.status_code == 400


def test_download_rejects_bad_format(client):
    res = client.post("/api/download", json={"url": "https://youtu.be/x", "format": "avi"})
    assert res.status_code == 400


def test_download_job_lifecycle(client, monkeypatch, tmp_path):
    class FakeYDL:
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
            return {"requested_downloads": [{"filepath": str(out)}]}

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FakeYDL)
    monkeypatch.setattr("app.jobs", downloader.JobManager(tmp_path))

    job = client.post("/api/download", json={"url": "https://youtu.be/x", "format": "mp4", "resolution": "720"}).get_json()
    import time

    for _ in range(50):
        state = client.get(f"/api/progress/{job['id']}").get_json()
        if state["status"] in ("completato", "errore"):
            break
        time.sleep(0.05)
    assert state["status"] == "completato"
    assert state["filename"] == "video [x].mp4"
    assert state["percent"] == 100.0
    assert (tmp_path / "video [x].mp4").read_bytes() == b"data"
    # la cartella temporanea viene rimossa
    assert [p.name for p in tmp_path.iterdir()] == ["video [x].mp4"]


def test_unique_path(tmp_path):
    (tmp_path / "a.mp4").write_text("x")
    (tmp_path / "a (1).mp4").write_text("x")
    assert downloader._unique_path(tmp_path / "a.mp4").name == "a (2).mp4"
    assert downloader._unique_path(tmp_path / "b.mp4").name == "b.mp4"


def test_progress_unknown_job(client):
    assert client.get("/api/progress/nope").status_code == 404


def test_open_folder_disabled_in_container(client, monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "CAN_OPEN_FOLDER", False)
    data = client.post("/api/open-folder", json={}).get_json()
    assert data["ok"] is False
