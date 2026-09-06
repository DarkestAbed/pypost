"""Test suite for pypost. Run from the repo root: `uv run --group dev pytest -q`"""
import asyncio
import xml.etree.ElementTree as ET

import main
from starlette.testclient import TestClient

client = TestClient(main.app)

CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


# ── Pages ──────────────────────────────────────────────────────────────────────

def test_index_pages():
    for path, marker in [("/", "Publicaciones recientes"), ("/en/", "Recent posts")]:
        r = client.get(path)
        assert r.status_code == 200
        assert marker in r.text


def test_all_posts_render():
    posts = [
        ("/posts/es/bienvenida", "Bienvenido a pypost"),
        ("/posts/es/demo-caracteristicas", "Demo de características"),
        ("/posts/en/welcome", "Welcome to pypost"),
        ("/posts/en/features-demo", "Features Demo"),
    ]
    for path, marker in posts:
        r = client.get(path)
        assert r.status_code == 200
        assert marker in r.text


def test_about_pages():
    assert client.get("/pages/es/about").status_code == 200
    assert client.get("/pages/en/about").status_code == 200


def test_missing_post_is_404():
    r = client.get("/posts/es/no-existe")
    assert r.status_code == 404
    assert "site-nav" in r.text  # styled, not a bare Starlette 404


def test_missing_page_is_404():
    assert client.get("/pages/es/missing-page").status_code == 404


def test_unknown_path_is_styled_404():
    for path in ("/whatever", "/en/whatever"):
        r = client.get(path)
        assert r.status_code == 404
        assert "site-nav" in r.text


def test_no_slash_redirects():
    for path, target in [("/tags", "/tags/"), ("/en", "/en/"),
                         ("/posts/es", "/posts/es/"), ("/en/tags", "/en/tags/")]:
        r = client.get(path, follow_redirects=False)
        assert r.status_code in (301, 302, 303, 307, 308)
        assert target in r.headers.get("location", "")


# ── Language handling ──────────────────────────────────────────────────────────

def test_html_lang_attribute():
    assert 'lang="es"' in client.get("/").text
    assert 'lang="en"' in client.get("/en/").text


def test_theme_cookie_applied_server_side():
    themed = TestClient(main.app, cookies={"theme": "light"})
    r = themed.get("/")
    assert 'data-theme="light"' in r.text


def test_translation_toggle_hrefs():
    r = client.get("/posts/es/demo-caracteristicas")
    assert 'href="/posts/en/features-demo" class="lang-btn"' in r.text
    r = client.get("/posts/en/features-demo")
    assert 'href="/posts/es/demo-caracteristicas" class="lang-btn"' in r.text


# ── Tags ───────────────────────────────────────────────────────────────────────

def test_tags_index_localized():
    assert "Todos los temas" in client.get("/tags/").text
    assert "All topics" in client.get("/en/tags/").text


def test_tag_view_by_slug():
    r = client.get("/tags/demo")
    assert r.status_code == 200
    assert "Artículos sobre #demo" in r.text
    assert "Posts tagged #demo" in client.get("/en/tags/demo").text


def test_unknown_tag_slug_is_404():
    assert client.get("/tags/nosuchtag").status_code == 404


# ── Feeds, sitemap, robots ─────────────────────────────────────────────────────

def test_rss_feeds():
    for path in ("/feed.xml", "/feed/es.xml", "/feed/en.xml"):
        r = client.get(path)
        assert r.status_code == 200
        channel = ET.fromstring(r.text).find("channel")
        assert channel.find("lastBuildDate") is not None
        assert main.SITE_URL in channel.find("link").text
        items = channel.findall("item")
        assert items
        assert items[0].find(f"{CONTENT_NS}encoded") is not None


def test_sitemap():
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    locs = [u.findtext(f"{SITEMAP_NS}loc") for u in ET.fromstring(r.text).findall(f"{SITEMAP_NS}url")]
    for expected in ("/posts/es/bienvenida", "/posts/en/welcome",
                     "/pages/es/about", "/pages/en/about", "/en/", "/"):
        assert f"{main.SITE_URL}{expected}" in locs


def test_robots_txt():
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert f"Sitemap: {main.SITE_URL}/sitemap.xml" in r.text


# ── Static files & security ────────────────────────────────────────────────────

def test_static_assets():
    for f in ("/static/custom.css", "/static/vendor/pico.classless.min.css",
              "/static/fonts/inter-var.woff2", "/static/favicon.svg",
              "/static/pygments.css"):
        assert client.get(f).status_code == 200


def _raw_status(path: str) -> int:
    "Call the app with a literal (undecoded) path, bypassing any client normalization."
    scope = {"type": "http", "http_version": "1.1", "method": "GET",
             "path": path, "raw_path": path.encode(), "query_string": b"",
             "headers": [], "root_path": "", "scheme": "http",
             "client": ("testclient", 50000), "server": ("testserver", 80)}
    status = {}
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    async def send(msg):
        if msg["type"] == "http.response.start":
            status["code"] = msg["status"]
    asyncio.run(main.app(scope, receive, send))
    return status["code"]


def test_path_traversal_blocked():
    for path in ("/static/../config.py", "/static/../.sesskey",
                 "/static/../../etc/passwd", "/static/..%2fmain.py"):
        assert _raw_status(path) == 404, path


def test_page_slug_traversal_blocked():
    assert _raw_status("/pages/es/..") == 404


def test_security_headers():
    r = client.get("/")
    assert "default-src 'self'" in r.headers.get("content-security-policy", "")
    assert r.headers.get("x-content-type-options") == "nosniff"


def test_cache_headers():
    r = client.get("/static/fonts/inter-var.woff2")
    assert "immutable" in r.headers.get("cache-control", "")
    r = client.get("/static/custom.css")
    assert "max-age=86400" in r.headers.get("cache-control", "")


def test_no_external_asset_urls():
    html = client.get("/").text
    assert "cdn.jsdelivr.net" not in html
    assert "fonts.googleapis.com" not in html


# ── Series ──────────────────────────────────────────────────────────────────────

def test_series_cross_language_nav():
    # The two demo posts share a series; part 1 (ES) ↔ part 2 (EN)
    r = client.get("/posts/es/demo-caracteristicas")
    assert 'class="series-nav"' in r.text
    assert 'href="/posts/en/features-demo"' in r.text
    r = client.get("/posts/en/features-demo")
    assert 'class="series-nav"' in r.text
    assert 'href="/posts/es/demo-caracteristicas"' in r.text


def test_series_label_shows_part():
    r = client.get("/posts/es/demo-caracteristicas")
    assert "Parte 1: Primeros pasos" in r.text


# ── Pagination ──────────────────────────────────────────────────────────────────

def test_pagination_hidden_when_single_page():
    assert 'class="pagination"' not in client.get("/").text


def test_out_of_range_page_is_404():
    assert client.get("/?page=9").status_code == 404
    assert client.get("/?page=0").status_code == 404


def test_pagination_nav():
    orig = main.POSTS_PER_PAGE
    main.POSTS_PER_PAGE = 2
    try:
        xml = main.to_xml(main.pagination_nav("es", 1, 5))
        assert "page=2" in xml and "page=1" not in xml
        xml = main.to_xml(main.pagination_nav("es", 2, 5))
        assert "page=1" in xml and "page=3" in xml
        assert main.pagination_nav("es", 1, 2) == ""
    finally:
        main.POSTS_PER_PAGE = orig