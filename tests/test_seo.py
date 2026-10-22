import re
import xml.etree.ElementTree as ET

import pytest

import app as app_module
import seo
from app import app

LANGUAGES = seo.LANGUAGES


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize(
    "headers,query,expected",
    [
        ({"Accept-Language": "de-DE,de;q=0.9"}, "", "/de/"),
        ({"Accept-Language": "ja"}, "", "/en/"),
        ({}, "?lang=fr", "/fr/"),
    ],
)
def test_home_redirects_to_language(client, headers, query, expected):
    res = client.get("/" + query, headers=headers)
    assert res.status_code == 302
    assert res.headers["Location"] == expected


@pytest.mark.parametrize("lang", LANGUAGES)
def test_home_page_is_rendered_in_its_language(client, lang):
    res = client.get(f"/{lang}/")
    assert res.status_code == 200
    page = res.get_data(as_text=True)
    assert f'<html lang="{lang}">' in page
    assert f"<title>{seo.t(lang, 'meta.title')}</title>" in page
    assert seo.t(lang, "faq.q2").replace("'", "&#x27;") in page or seo.t(lang, "faq.q2") in page
    assert f'<link rel="canonical" href="{seo.PUBLIC_URL}/{lang}/">' in page
    for code in LANGUAGES:
        assert f'hreflang="{code}" href="{seo.PUBLIC_URL}/{code}/"' in page
    assert 'hreflang="x-default"' in page
    assert 'property="og:image"' in page and 'name="description"' in page
    assert f'href="/note-legali?lang={lang}"' in page


def test_home_uses_language_chosen_in_menu(client):
    client.set_cookie("grabby-lang", "pt")
    res = client.get("/", headers={"Accept-Language": "it"})
    assert res.headers["Location"] == "/pt/"


def test_unknown_language_is_404(client):
    assert client.get("/xx/").status_code == 404


def test_rendered_text_matches_translations(client):
    page = client.get("/de/").get_data(as_text=True)
    assert ">Herunterladen</button>" in page
    assert 'placeholder="' + seo.t("de", "confirm.name.placeholder") + '"' in page
    # Nessun testo italiano rimasto negli elementi tradotti.
    for key in re.findall(r'data-i18n="([^"]+)"', page):
        if seo.t("de", key) != seo.t("it", key):
            assert f'data-i18n="{key}">{seo.t("it", key)}<' not in page, key


def test_translation_keys_stay_in_page(client):
    page = client.get("/fr/").get_data(as_text=True)
    assert 'data-i18n-href="legal"' in page and 'data-i18n-href="privacy"' in page
    assert 'data-i18n-placeholder="confirm.name.placeholder"' in page
    assert 'data-i18n-label="langs.label"' in page
    assert 'href="undefined"' not in page


def test_robots(client, monkeypatch):
    assert "Disallow: /\n" in client.get("/robots.txt").get_data(as_text=True)
    monkeypatch.setattr(app_module, "ONLINE", True)
    text = client.get("/robots.txt").get_data(as_text=True)
    assert "Disallow: /api/" in text
    assert f"Sitemap: {seo.PUBLIC_URL}/sitemap.xml" in text


def test_sitemap_lists_every_language(client):
    res = client.get("/sitemap.xml")
    assert res.mimetype == "application/xml"
    root = ET.fromstring(res.data)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [loc.text for loc in root.findall("s:url/s:loc", ns)]
    for code in LANGUAGES:
        assert f"{seo.PUBLIC_URL}/{code}/" in locs
        assert f"{seo.PUBLIC_URL}/note-legali?lang={code}" in locs


def test_legal_notes_have_hreflang(client):
    page = client.get("/note-legali?lang=fr").get_data(as_text=True)
    assert f'<link rel="canonical" href="{seo.PUBLIC_URL}/note-legali?lang=fr">' in page
    assert 'hreflang="de"' in page


def test_favicon_and_preview_image(client):
    assert client.get("/favicon.ico").status_code == 200
    assert client.get("/static/og-image.png").status_code == 200
