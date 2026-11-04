#!/usr/bin/env python3
"""Baut die statische Seite aus src/ nach public/. Nur Standardbibliothek.

Jede Datei in src/pages beginnt mit einer JSON-Zeile (Titel, Beschreibung, Pfad).
Platzhalter im Text:
  {{img:name|Alt-Text|sizes}}   Foto mit 800/1600er-Quelle
  {{hero:name|Alt-Text}}        wie img, aber sofort geladen
  {{preise:Gruppe}}             Preisliste aus src/preise.json
  {{mail}} {{tel}} {{tel_link}} {{site}}
"""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
from html import escape

SITE = "https://propertale.de"
MAIL = "info@propertale.de"
TEL = "0171 8181922"
TEL_LINK = "+491718181922"
INSTAGRAM = "https://www.instagram.com/propertale.media/"

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "public"
NAV = [("/leistungen/", "Leistungen & Preise"), ("/referenzen/", "Referenzen"), ("/ablauf/", "Ablauf")]
PRICES = json.loads((SRC / "preise.json").read_text("utf-8"))
# Neue Fassung, neue Adresse: Browser laden geänderte Formatierung sofort.
CSS_VERSION = hashlib.sha256((SRC / "assets/css/style.css").read_bytes()).hexdigest()[:8]


def euro(value):
    text = f"{value:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return text.removesuffix(",00") + " €"


def price_label(entry):
    label = euro(entry["price"])
    if entry["from"]:
        label = "ab " + label
    if entry["unit"] != "Pauschale":
        label += " / " + entry["unit"]
    return label


def price_table(group):
    rows = []
    for entry in (e for e in PRICES if e["group"] == group):
        title = entry["title"].split(" – ", 1)[-1] if group != "Zusatzleistungen" else entry["title"]
        text = f'<span>{escape(entry["text"])}</span>' if entry["text"] else ""
        rows.append(f'<li><div><strong>{escape(title)}</strong>{text}</div><b>{price_label(entry)}</b></li>')
    if not rows:
        raise SystemExit(f"Keine Preise für Gruppe {group}")
    return '<ul class="preise">' + "".join(rows) + "</ul>"


def picture(name, alt, sizes="100vw", eager=False):
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img src="/assets/img/{name}-1600.jpg" srcset="/assets/img/{name}-800.jpg 800w, '
            f'/assets/img/{name}-1600.jpg 1600w" sizes="{sizes}" width="1600" height="1066" '
            f'alt="{escape(alt)}" {load}>')


def fill(text):
    text = re.sub(r"\{\{img:([^|}]+)\|([^|}]+)(?:\|([^}]+))?\}\}",
                  lambda m: picture(m[1], m[2], m[3] or "100vw"), text)
    text = re.sub(r"\{\{hero:([^|}]+)\|([^}]+)\}\}", lambda m: picture(m[1], m[2], eager=True), text)
    text = re.sub(r"\{\{preise:([^}]+)\}\}", lambda m: price_table(m[1]), text)
    for key, value in {"mail": MAIL, "tel": TEL, "tel_link": TEL_LINK, "site": SITE, "instagram": INSTAGRAM}.items():
        text = text.replace("{{" + key + "}}", value)
    if "{{" in text:
        raise SystemExit("Unbekannter Platzhalter: " + text[text.index("{{"):][:40])
    return text


HERO = "immobilienfoto-wintergarten-treppe"

# Wortmarke aus Documents/claude_skills/Propertale-Logo/wortmarke.svg (Work Sans als Pfade, A als Dach),
# direkt in die Seite gesetzt, damit sie die Textfarbe übernimmt.
WORDMARK = (SRC / "assets/img/wortmarke.svg").read_text("utf-8").strip().replace(
    "<svg ", '<svg class="wortmarke" aria-hidden="true" ', 1)

LOCAL_BUSINESS = json.dumps({
    "@context": "https://schema.org",
    "@type": ["LocalBusiness", "ProfessionalService"],
    "@id": SITE + "/#business",
    "name": "Propertale",
    "description": "Immobilienfotografie, Video und Drohnenaufnahmen für Makler und private Eigentümer im Rhein-Main-Gebiet.",
    "url": SITE + "/",
    "email": MAIL,
    "telephone": TEL_LINK,
    "image": f"{SITE}/assets/img/{HERO}-1600.jpg",
    "logo": SITE + "/assets/img/logo-512.png",
    "priceRange": "€€",
    "address": {"@type": "PostalAddress", "streetAddress": "Lerchenstr. 5", "postalCode": "64823",
                "addressLocality": "Groß-Umstadt", "addressRegion": "Hessen", "addressCountry": "DE"},
    "areaServed": ["Rhein-Main-Gebiet", "Frankfurt am Main", "Darmstadt", "Wiesbaden", "Mainz", "Offenbach am Main", "Hanau"],
    "sameAs": [INSTAGRAM],
}, ensure_ascii=False)


def offer(entry):
    spec = {"@type": "PriceSpecification", "priceCurrency": "EUR"}
    spec["minPrice" if entry["from"] else "price"] = entry["price"]
    return {"@type": "Offer", "priceSpecification": spec,
            "itemOffered": {"@type": "Service", "name": entry["title"], "description": entry["text"] or entry["title"]}}


def structured_data(meta):
    path = meta["path"]
    if path == "/":
        return [LOCAL_BUSINESS]
    blocks = []
    if meta.get("crumb"):
        blocks.append(json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Start", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": meta["crumb"], "item": SITE + path},
        ]}, ensure_ascii=False))
    if path == "/leistungen/":
        blocks.append(json.dumps({"@context": "https://schema.org", "@type": "ProfessionalService",
                                  "@id": SITE + "/#business", "name": "Propertale", "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Leistungen und Preise",
            "itemListElement": [offer(e) for e in PRICES]}}, ensure_ascii=False))
    return blocks


def last_change(file):
    """Datum der letzten Änderung laut Git, damit die Sitemap nicht bei jedem Build neu datiert."""
    day = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(file)], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    return f"<lastmod>{day}</lastmod>" if day else ""


def page(meta, body):
    path = meta["path"]
    nav = "".join(f'<a href="{href}"{" aria-current=page" if href == path else ""}>{escape(label)}</a>'
                  for href, label in NAV)
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
    ld = "".join(f'<script type="application/ld+json">{block}</script>' for block in structured_data(meta))
    preload = (f'<link rel="preload" as="image" href="/assets/img/{HERO}-1600.jpg" imagesizes="100vw" '
               f'imagesrcset="/assets/img/{HERO}-800.jpg 800w, /assets/img/{HERO}-1600.jpg 1600w">') if path == "/" else ""
    canonical = f'<link rel="canonical" href="{SITE}{path}">' if not meta.get("noindex") else ""
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(meta["title"])}</title>
<meta name="description" content="{escape(meta["description"])}">
{canonical}{robots}
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="Propertale">
<meta property="og:title" content="{escape(meta["title"])}">
<meta property="og:description" content="{escape(meta["description"])}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}/assets/img/{HERO}-1600.jpg">
<meta property="og:image:width" content="1600">
<meta property="og:image:height" content="1066">
<meta property="og:image:alt" content="Helles Wohnhaus mit Wintergarten und Holztreppe, fotografiert von Propertale">
<meta name="twitter:card" content="summary_large_image">
{preload}
<meta name="theme-color" content="#f3efe6">
<link rel="icon" href="/assets/img/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/Manrope.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css?v={CSS_VERSION}">
{ld}
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt</a>
<header class="kopf">
  <a class="marke" href="/" aria-label="Propertale, Startseite">{WORDMARK}</a>
  <button class="menue" aria-expanded="false" aria-controls="nav">Menü</button>
  <nav id="nav" aria-label="Hauptnavigation">{nav}<a class="anfrage" href="/kontakt/">Anfrage</a></nav>
</header>
<main id="inhalt">
{body}
</main>
<footer class="fuss">
  <div class="fuss-gross"><p>Immobilien sichtbar machen.</p><a class="knopf hell" href="/kontakt/">Shooting anfragen</a></div>
  <div class="fuss-spalten">
    <div><a class="marke" href="/" aria-label="Propertale, Startseite">{WORDMARK}</a><p>Immobilienfotografie<br>Rhein-Main-Gebiet</p></div>
    <div><a href="mailto:{MAIL}">{MAIL}</a><br><a href="tel:{TEL_LINK}">{TEL}</a><br><a href="{INSTAGRAM}" rel="noopener">Instagram @propertale.media</a></div>
    <div><a href="/immobilienfotograf-rhein-main/">Region</a><br><a href="/haeufige-fragen/">Häufige Fragen</a></div>
    <div><a href="/impressum/">Impressum</a><br><a href="/datenschutz/">Datenschutz</a><br><a href="/widerruf/">Widerruf</a></div>
  </div>
</footer>
<script src="/assets/js/main.js" defer></script>
</body>
</html>
"""


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(SRC / "assets", OUT / "assets")
    for name in ("kontakt.php", ".htaccess", "robots.txt"):
        shutil.copy(SRC / name, OUT / name)

    urls = []
    for file in sorted((SRC / "pages").glob("*.html")):
        head, body = file.read_text("utf-8").split("\n", 1)
        meta = json.loads(head)
        html = page(meta, fill(body))
        target = OUT / "404.html" if meta["path"] == "/404/" else OUT / meta["path"].strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, "utf-8")
        if not meta.get("noindex"):
            urls.append(f"<url><loc>{SITE}{meta['path']}</loc>{last_change(file)}</url>")

    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls) + "</urlset>\n", "utf-8")
    print(f"{len(urls)} Seiten in der Sitemap, Ausgabe in {OUT}")


if __name__ == "__main__":
    main()
