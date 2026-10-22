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


@pytest.mark.parametrize("lang", ["en", "es", "fr", "de", "pt"])
def test_legal_notes_translated(client, lang):
    page = client.get(f"/note-legali?lang={lang}").get_data(as_text=True)
    assert f'<html lang="{lang}"' in page
    assert 'id="casi-consentiti"' in page
    assert "/static/pagine-legali.js" in page


def test_legal_notes_language_fallback(client):
    assert '<html lang="it"' in client.get("/note-legali").get_data(as_text=True)
    assert '<html lang="it"' in client.get("/note-legali?lang=xx").get_data(as_text=True)
    page = client.get("/note-legali", headers={"Accept-Language": "de-DE,de;q=0.9"}).get_data(as_text=True)
    assert '<html lang="de"' in page


def test_legal_translations_keep_structure():
    """Ogni traduzione ha le stesse sezioni, scenari e righe di tabella dell'originale."""
    original = (STATIC / "note-legali.html").read_text(encoding="utf-8")
    for lang in ("en", "es", "fr", "de", "pt"):
        page = (STATIC / f"note-legali.{lang}.html").read_text(encoding="utf-8")
        for tag in ("<section", 'class="scenario"', "<tr>", "<li>", "<blockquote>", 'href="http'):
            assert page.count(tag) == original.count(tag), (lang, tag)
        assert 'data-translations="it en es fr de pt"' in page


def test_log_records_page_language():
    import app as app_module

    assert app_module._log_language("en", "it-IT") == "en (browser: it-IT)"
    assert app_module._log_language("it", "it") == "it"
    assert app_module._log_language(None, "it-IT") == "it-IT"
    assert app_module._log_language("xx", "it-IT") == "it-IT"
