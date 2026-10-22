import json
import re
from pathlib import Path

import pytest

from app import app
from tests.helpers import download_request

STATIC = Path(__file__).resolve().parent.parent / "static"
LANGUAGES = {"it": "it", "en": "gb", "es": "es", "fr": "fr", "de": "de", "pt": "pt"}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def _strings() -> dict:
    """Legge il dizionario STRINGS di i18n.js (le chiavi e i testi sono stringhe JSON)."""
    source = (STATIC / "i18n.js").read_text(encoding="utf-8")
    strings = {}
    for lang, body in re.findall(r"^    (\w\w): \{\n(.*?)\n    \},", source, re.S | re.M):
        strings[lang] = json.loads("{" + body.rstrip().rstrip(",") + "}")
    return strings


def test_every_language_has_every_string():
    strings = _strings()
    assert set(strings) == set(LANGUAGES)
    for lang, texts in strings.items():
        assert set(texts) == set(strings["it"]), lang
        assert all(texts.values()), lang


def test_page_keys_exist():
    keys = set(_strings()["it"])
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    used = set(re.findall(r'data-i18n(?:-html|-placeholder)?="([^"]+)"', page))
    used |= set(re.findall(r'\bt\("([a-z0-9_.]+[a-z0-9_])"', page))
    assert used <= keys, used - keys


def test_flags_and_scripts_are_served(client):
    for flag in LANGUAGES.values():
        assert client.get(f"/static/flags/{flag}.svg").status_code == 200
    assert client.get("/static/i18n.js").status_code == 200
    assert client.get("/static/pagine-legali.js").status_code == 200


@pytest.mark.parametrize(
    "overrides,code",
    [
        ({"url": "https://example.com/v"}, "invalid_url"),
        ({"name": ""}, "name_required"),
        ({"accepted": False}, "not_accepted"),
        ({"format": "avi"}, "invalid_option"),
    ],
)
def test_errors_have_translatable_code(client, overrides, code):
    res = client.post("/api/download", json=download_request(**overrides))
    assert res.status_code == 400
    data = res.get_json()
    assert data["code"] == code
    assert data["error"]
    assert f"err.{code}" in _strings()["en"]


def test_progress_not_found_code(client):
    assert client.get("/api/progress/nope").get_json()["code"] == "not_found"
