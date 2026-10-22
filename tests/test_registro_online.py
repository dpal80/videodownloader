import csv
from datetime import datetime, timedelta

import pytest

import app as app_module
import downloader
from registro import COLUMNS, DownloadLog
from tests.helpers import download_request, wait_for


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def read_log(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


@pytest.mark.parametrize("field,value", [("accepted", False), ("accepted", None), ("name", "   ")])
def test_download_requires_acceptance_and_name(client, field, value):
    res = client.post("/api/download", json=download_request(**{field: value}))
    assert res.status_code == 400


def test_options_include_declaration(client):
    data = client.get("/api/options").get_json()
    assert "piena responsabilità" in data["declaration"]
    assert data["online"] is False


def test_download_is_logged(client, fake_ydl, monkeypatch, tmp_path):
    log = DownloadLog(tmp_path / "registro.csv")
    monkeypatch.setattr(app_module, "jobs", downloader.JobManager(tmp_path / "out", log=log))

    res = client.post(
        "/api/download",
        json=download_request(),
        headers={"User-Agent": "Browser di prova", "Accept-Language": "it-IT"},
    )
    assert wait_for(client, res.get_json()["id"])["status"] == "completato"

    rows = read_log(log.path)
    assert [r["evento"] for r in rows] == ["richiesto", "completato"]
    done = rows[-1]
    assert done["nome"] == "Mario Rossi"
    assert done["ip"] == "127.0.0.1"
    assert done["browser"] == "Browser di prova"
    assert done["lingua"] == "it-IT"
    assert done["dichiarazione"].startswith("accettata v")
    assert done["titolo"] == "Video di prova"
    assert done["file"] == "video [x].mp4"


def test_log_neutralizes_spreadsheet_formulas(tmp_path):
    log = DownloadLog(tmp_path / "r.csv")
    log.record({"nome": "=HYPERLINK(\"x\")", "link": "https://youtu.be/x"})
    assert read_log(log.path)[0]["nome"].startswith("'=")


def test_log_retention_purges_old_rows(tmp_path):
    log = DownloadLog(tmp_path / "r.csv", retention_days=30)
    with open(log.path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";")
        w.writeheader()
        w.writerow({"data_ora": (datetime.now() - timedelta(days=45)).isoformat(timespec="seconds"), "nome": "vecchio"})
        w.writerow({"data_ora": (datetime.now() - timedelta(days=5)).isoformat(timespec="seconds"), "nome": "recente"})
    assert log.purge() == 1
    assert [r["nome"] for r in read_log(log.path)] == ["recente"]


@pytest.fixture
def online(monkeypatch, tmp_path, fake_ydl):
    monkeypatch.setattr(app_module, "ONLINE", True)
    monkeypatch.setattr(app_module, "CAN_OPEN_FOLDER", False)
    monkeypatch.setattr(app_module, "download_limiter", app_module.RateLimiter(3))
    manager = downloader.JobManager(tmp_path / "server", log=DownloadLog(tmp_path / "r.csv"))
    monkeypatch.setattr(app_module, "jobs", manager)
    return manager


def test_online_serves_file_and_deletes_it(client, online, tmp_path):
    job = client.post("/api/download", json=download_request()).get_json()
    state = wait_for(client, job["id"])
    assert state["status"] == "completato"
    assert "filepath" not in state  # il percorso sul server resta privato

    res = client.get(f"/api/file/{job['id']}")
    assert res.status_code == 200
    assert res.data == b"data"
    assert "attachment" in res.headers["Content-Disposition"]
    res.close()
    assert not (tmp_path / "server" / "video [x].mp4").exists()
    # una seconda volta non c'è più
    assert client.get(f"/api/file/{job['id']}").status_code == 404


def test_online_file_only_for_requesting_ip(client, online):
    job = client.post("/api/download", json=download_request()).get_json()
    wait_for(client, job["id"])
    res = client.get(f"/api/file/{job['id']}", environ_base={"REMOTE_ADDR": "10.0.0.9"})
    assert res.status_code == 404


def test_online_rate_limit(client, online):
    for _ in range(3):
        job = client.post("/api/download", json=download_request()).get_json()
        wait_for(client, job["id"])
    assert client.post("/api/download", json=download_request()).status_code == 429


def test_file_endpoint_disabled_locally(client, fake_ydl, monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "jobs", downloader.JobManager(tmp_path))
    job = client.post("/api/download", json=download_request()).get_json()
    wait_for(client, job["id"])
    assert client.get(f"/api/file/{job['id']}").status_code == 404


def test_rate_limiter_window():
    limiter = app_module.RateLimiter(2, window=3600)
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")


def test_log_time_has_timezone(tmp_path):
    log = DownloadLog(tmp_path / "r.csv", retention_days=30)
    log.record({"nome": "x"})
    assert datetime.fromisoformat(read_log(log.path)[0]["data_ora"]).tzinfo is not None
