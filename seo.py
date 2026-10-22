"""Pagine pronte per i motori di ricerca.

La pagina principale esce dal server già tradotta nella lingua dell'indirizzo
(/it/, /en/, /de/...), con i tag che Google e i social leggono: descrizione,
indirizzo canonico, versioni nelle altre lingue (hreflang) e anteprima Open
Graph. I testi sono quelli di static/i18n.js, così pagina e browser dicono
sempre la stessa cosa.
"""
import html
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

STATIC = Path(__file__).resolve().parent / "static"
# Devono coincidere con LANGUAGES in static/i18n.js.
LANGUAGES = ("it", "en", "es", "fr", "de", "pt")
DEFAULT_LANGUAGE = "en"
OG_LOCALES = {"it": "it_IT", "en": "en_GB", "es": "es_ES", "fr": "fr_FR", "de": "de_DE", "pt": "pt_PT"}
PUBLIC_URL = os.environ.get("GRABBY_URL_PUBBLICO", "https://grabbyvideodownloader.app").rstrip("/")


@lru_cache(maxsize=None)
def strings() -> dict:
    """Legge il dizionario STRINGS di i18n.js: chiavi e testi sono stringhe JSON."""
    source = (STATIC / "i18n.js").read_text(encoding="utf-8")
    found = {}
    for lang, body in re.findall(r"^    (\w\w): \{\n(.*?)\n    \},", source, re.S | re.M):
        found[lang] = json.loads("{" + body.rstrip().rstrip(",") + "}")
    return found


def t(lang: str, key: str, **values) -> str:
    text = strings()[lang].get(key) or strings()[DEFAULT_LANGUAGE].get(key, key)
    return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), m.group(0))), text)


def legal_links(lang: str) -> dict:
    return {"legal": f"/note-legali?lang={lang}", "privacy": f"/privacy?lang={lang}"}


def _element(attribute: str):
    # Un elemento con l'attributo indicato e il suo contenuto, fino al tag di chiusura.
    return re.compile(rf'(<(\w+)\b[^>]*\s{attribute}="([^"]+)"[^>]*>)(.*?)(</\2>)', re.S)


def _translate_body(page: str, lang: str) -> str:
    links = legal_links(lang)
    page = _element("data-i18n").sub(
        lambda m: m.group(1) + html.escape(t(lang, m.group(3)), quote=False) + m.group(5), page)
    # Testi con link: vengono solo da i18n.js, mai da dati degli utenti.
    page = _element("data-i18n-html").sub(
        lambda m: m.group(1) + t(lang, m.group(3), **links) + m.group(5), page)

    def fix_tag(match):
        tag = match.group(0)
        if key := re.search(r'data-i18n-placeholder="([^"]+)"', tag):
            tag = re.sub(r'(?<![\w-])placeholder="[^"]*"', f'placeholder="{html.escape(t(lang, key.group(1)))}"', tag)
        if key := re.search(r'data-i18n-label="([^"]+)"', tag):
            tag = re.sub(r'(?<![\w-])aria-label="[^"]*"', f'aria-label="{html.escape(t(lang, key.group(1)))}"', tag)
        if key := re.search(r'data-i18n-href="([^"]+)"', tag):
            tag = re.sub(r'(?<![\w-])href="[^"]*"', f'href="{links[key.group(1)]}"', tag)
        return tag

    return re.sub(r"<[a-z]+\b[^>]*data-i18n-(?:placeholder|label|href)=[^>]*>", fix_tag, page)


def _alternates(path_for) -> str:
    links = [f'<link rel="alternate" hreflang="{code}" href="{PUBLIC_URL}{path_for(code)}">' for code in LANGUAGES]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{PUBLIC_URL}{path_for(None)}">')
    return "\n  ".join(links)


def home_page(lang: str) -> str:
    """La pagina principale nella lingua indicata, con i tag per motori di ricerca e social."""
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    title = html.escape(t(lang, "meta.title"))
    description = html.escape(t(lang, "meta.description"))
    url = f"{PUBLIC_URL}/{lang}/"
    image = f"{PUBLIC_URL}/static/og-image.png"
    app_data = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Grabby Video Downloader",
        "url": url,
        "description": t(lang, "meta.description"),
        "inLanguage": lang,
        "applicationCategory": "MultimediaApplication",
        "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
    }, ensure_ascii=False).replace("</", "<\\/")
    other_locales = "\n  ".join(
        f'<meta property="og:locale:alternate" content="{OG_LOCALES[code]}">' for code in LANGUAGES if code != lang)
    head = f"""<title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{url}">
  {_alternates(lambda code: f"/{code}/" if code else "/")}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Grabby Video Downloader">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Grabby Video Downloader">
  <meta property="og:locale" content="{OG_LOCALES[lang]}">
  {other_locales}
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">{app_data}</script>"""
    page = page.replace('<html lang="it">', f'<html lang="{lang}">', 1)
    page = re.sub(r"<title>.*?</title>", lambda _: head, page, count=1)
    return _translate_body(page, lang)


def legal_head(lang: str) -> str:
    """Indirizzo canonico e versioni nelle altre lingue delle note legali."""
    return (f'<link rel="canonical" href="{PUBLIC_URL}/note-legali?lang={lang}">\n'
            + _alternates(lambda code: f"/note-legali?lang={code}" if code else "/note-legali") + "\n")


def robots_txt(online: bool) -> str:
    if not online:
        # In locale Grabby non è un sito pubblico: niente indicizzazione.
        return "User-agent: *\nDisallow: /\n"
    return f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {PUBLIC_URL}/sitemap.xml\n"


def sitemap_xml() -> str:
    def entry(path_for) -> str:
        alternates = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{code}" href="{xml_escape(PUBLIC_URL + path_for(code))}"/>'
            for code in LANGUAGES)
        return "".join(
            f"\n  <url>\n    <loc>{xml_escape(PUBLIC_URL + path_for(code))}</loc>{alternates}\n  </url>"
            for code in LANGUAGES)

    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'
            + entry(lambda code: f"/{code}/")
            + entry(lambda code: f"/note-legali?lang={code}")
            + f"\n  <url>\n    <loc>{PUBLIC_URL}/privacy</loc>\n  </url>\n</urlset>\n")
