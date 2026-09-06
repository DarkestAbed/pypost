import os
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from email.utils import formatdate
from datetime import datetime

import frontmatter as fm
import mistune
from pygments import highlight as pygments_highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from fasthtml.common import *

from config import (
    SITE_NAME, SITE_DESCRIPTION, AUTHOR, PORT,
    DEFAULT_LANG, SUPPORTED_LANGS, NAV_LINKS, UI_STRINGS,
)

# ── Syntax-highlighting Markdown renderer ─────────────────────────────────────

class TechnicalRenderer(mistune.HTMLRenderer):
    def block_code(self, code: str, info: str = None, **attrs) -> str:
        lang_clean = (info or "").strip().split()[0] if info else ""
        try:
            lexer = get_lexer_by_name(lang_clean) if lang_clean else TextLexer()
        except ClassNotFound:
            lexer = TextLexer()
        formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
        highlighted = pygments_highlight(code, lexer, formatter)
        label = f'<span class="code-lang">{lang_clean}</span>' if lang_clean else ""
        copy_btn = '<button class="copy-btn" onclick="copyCode(this)" aria-label="Copy code">copy</button>'
        return f'<div class="code-block">{label}{copy_btn}{highlighted}</div>\n'

    def heading(self, text: str, level: int, **attrs) -> str:
        plain = re.sub(r"<[^>]+>", "", text)
        anchor = _slugify(plain)
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'


_md_renderer = TechnicalRenderer()
md = mistune.create_markdown(
    renderer=_md_renderer,
    plugins=["table", "strikethrough", "task_lists"],
)

# ── Pygments CSS (generated once at startup) ──────────────────────────────────

_dark_css  = HtmlFormatter(style="monokai",  cssclass="highlight").get_style_defs(".highlight")
_light_css = HtmlFormatter(style="friendly", cssclass="highlight").get_style_defs(".highlight")

PYGMENTS_CSS = (
    f"[data-theme='dark'] .highlight {{ background: var(--code-bg); }}\n"
    f"[data-theme='dark'] {_dark_css}\n"
    f"[data-theme='light'] {_light_css}\n"
)

_pygments_path = Path("static/pygments.css")
_pygments_path.parent.mkdir(exist_ok=True)
_pygments_path.write_text(PYGMENTS_CSS)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text)


class _TagStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str):
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(html: str) -> str:
    p = _TagStripper()
    p.feed(html)
    return p.get_text()


def reading_time(html: str) -> int:
    words = len(_strip_html(html).split())
    return max(1, round(words / 200))


def build_toc(html: str) -> list[dict]:
    toc = []
    for m in re.finditer(r'<h([23])[^>]*id="([^"]+)"[^>]*>(.*?)</h\1>', html, re.DOTALL):
        level  = int(m.group(1))
        anchor = m.group(2)
        text   = re.sub(r"<[^>]+>", "", m.group(3)).strip()
        toc.append({"level": level, "anchor": anchor, "text": text})
    return toc


# ── Post loading ──────────────────────────────────────────────────────────────

_MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _format_date(raw, lang: str) -> str:
    if not raw:
        return ""
    if hasattr(raw, "strftime"):
        if lang == "es":
            return f"{raw.day} de {_MONTHS_ES[raw.month]} de {raw.year}"
        return raw.strftime("%B %d, %Y")
    return str(raw)


def load_posts(lang: str) -> list[dict]:
    base = Path("posts") / lang
    if not base.exists():
        return []
    posts = []
    seen_slugs: dict[str, str] = {}

    for path in base.glob("*.md"):
        post = fm.load(str(path))
        if not post.get("published", False):
            continue

        title = post.get("title", path.stem)
        slug  = post.get("slug") or _slugify(title)

        if slug in seen_slugs:
            raise ValueError(
                f"Slug collision: '{slug}' from '{path}' conflicts with '{seen_slugs[slug]}'"
            )
        seen_slugs[slug] = str(path)

        raw_date     = post.get("date")
        content_html = md(post.content)

        posts.append({
            "slug":         slug,
            "title":        title,
            "date":         raw_date,
            "date_str":     _format_date(raw_date, lang),
            "author":       post.get("author", AUTHOR),
            "description":  post.get("description", ""),
            "tags":         post.get("tags", []),
            "series":       post.get("series", ""),
            "series_part":  post.get("series_part", None),
            "toc_enabled":  post.get("toc", True),
            "content_html": content_html,
            "reading_time": reading_time(content_html),
            "toc":          build_toc(content_html),
            "lang":         lang,
        })

    return sorted(posts, key=lambda p: p["date"] or datetime.min, reverse=True)


def load_page(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        return ""
    post = fm.load(str(path))
    return md(post.content)


# ── Indexes (built once at startup) ───────────────────────────────────────────

POST_INDEX: dict[str, dict[str, dict]] = {
    lang: {p["slug"]: p for p in load_posts(lang)}
    for lang in SUPPORTED_LANGS
}


def get_post(slug: str, lang: str) -> dict | None:
    return POST_INDEX.get(lang, {}).get(slug)


def get_all_posts(lang: str) -> list[dict]:
    return sorted(POST_INDEX.get(lang, {}).values(),
                  key=lambda p: p["date"] or datetime.min, reverse=True)


# Tag index: tag -> list of posts across all languages
TAG_INDEX: dict[str, list[dict]] = {}
for _lang in SUPPORTED_LANGS:
    for _post in POST_INDEX[_lang].values():
        for _tag in _post["tags"]:
            TAG_INDEX.setdefault(_tag, []).append(_post)
for _tag in TAG_INDEX:
    TAG_INDEX[_tag].sort(key=lambda p: p["date"] or datetime.min, reverse=True)


# Series index: series_name -> posts sorted by series_part
SERIES_INDEX: dict[str, list[dict]] = {}
for _lang in SUPPORTED_LANGS:
    for _post in POST_INDEX[_lang].values():
        if _post["series"]:
            SERIES_INDEX.setdefault(_post["series"], []).append(_post)
for _s in SERIES_INDEX:
    SERIES_INDEX[_s].sort(key=lambda p: p["series_part"] or 0)


def get_series_neighbors(post: dict) -> tuple[dict | None, dict | None]:
    if not post["series"]:
        return None, None
    members = SERIES_INDEX.get(post["series"], [])
    for i, p in enumerate(members):
        if p["slug"] == post["slug"] and p["lang"] == post["lang"]:
            prev_p = members[i - 1] if i > 0 else None
            next_p = members[i + 1] if i < len(members) - 1 else None
            return prev_p, next_p
    return None, None


# ── App setup ─────────────────────────────────────────────────────────────────

theme_init = Script("""
(function(){
  var m = document.cookie.match(/(?:^|;\\s*)theme=([^;]+)/);
  if (m) document.documentElement.setAttribute('data-theme', m[1]);
})();
""")

copy_script = Script("""
function copyCode(btn) {
  var block = btn.closest('.code-block').querySelector('.highlight pre');
  var text = block ? block.innerText : '';
  navigator.clipboard.writeText(text).then(function() {
    btn.textContent = 'copied!';
    setTimeout(function(){ btn.textContent = 'copy'; }, 1500);
  });
}
""")

pico_css    = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css")
pygments_css = Link(rel="stylesheet", href="/static/pygments.css")
custom_css  = Link(rel="stylesheet", href="/static/custom.css")
inter_font  = Link(
    rel="stylesheet",
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
)

app = FastHTML(
    hdrs=(theme_init, inter_font, pico_css, pygments_css, custom_css, copy_script),
    htmlkw={"data-theme": "dark"},
)

_secondary_lang = next(l for l in SUPPORTED_LANGS if l != DEFAULT_LANG)


# ── Components ────────────────────────────────────────────────────────────────

def _lang_toggle_href(path: str, current_lang: str) -> str:
    other = _secondary_lang if current_lang == DEFAULT_LANG else DEFAULT_LANG
    default_root = "/"
    other_root   = f"/{_secondary_lang}/"
    if path in (default_root, other_root):
        return other_root if other == _secondary_lang else default_root
    parts = path.split("/")
    for i, part in enumerate(parts):
        if part in SUPPORTED_LANGS:
            parts[i] = other
            return "/".join(parts)
    return other_root if other == _secondary_lang else default_root


def nav_bar(lang: str, current_path: str):
    s = UI_STRINGS[lang]
    links    = [Li(A(label, href=href)) for label, href in NAV_LINKS[lang]]
    lang_btn = A(s["switch_lang"], href=_lang_toggle_href(current_path, lang), cls="lang-btn")
    theme_btn = Button(
        s["toggle_theme"],
        cls="theme-btn",
        hx_post="/set-theme",
        hx_swap="none",
        hx_vals="js:{current_theme: document.documentElement.getAttribute('data-theme')}",
        onclick=(
            "var h=document.documentElement,"
            "n=h.getAttribute('data-theme')==='dark'?'light':'dark';"
            "h.setAttribute('data-theme',n);"
        ),
    )
    home_href = "/" if lang == DEFAULT_LANG else f"/{_secondary_lang}/"
    return Nav(
        Div(
            A(SITE_NAME, href=home_href, cls="nav-brand"),
            Ul(*links, cls="nav-links"),
            Div(lang_btn, theme_btn, cls="nav-controls"),
            cls="nav-inner",
        ),
        cls="site-nav",
    )


def site_footer(lang: str):
    return Footer(
        P(f"© {UI_STRINGS[lang]['footer']}"),
        cls="site-footer",
    )


def _og_tags(title: str, description: str, url: str):
    base_url = f"https://{SITE_NAME}"
    return (
        Meta(property="og:type",        content="article"),
        Meta(property="og:title",       content=f"{title} | {SITE_NAME}"),
        Meta(property="og:description", content=description),
        Meta(property="og:url",         content=f"{base_url}{url}"),
        Meta(name="description",        content=description),
        Link(rel="alternate", type="application/rss+xml",
             title=f"{SITE_NAME} {DEFAULT_LANG.upper()}", href="/feed.xml"),
        Link(rel="alternate", type="application/rss+xml",
             title=f"{SITE_NAME} {_secondary_lang.upper()}", href=f"/feed/{_secondary_lang}.xml"),
    )


def page_shell(title: str, lang: str, current_path: str, description: str = "", *content):
    return (
        Title(f"{title} | {SITE_NAME}"),
        *_og_tags(title, description, current_path),
        nav_bar(lang, current_path),
        Main(*content, cls="container"),
        site_footer(lang),
    )


def tag_badge(tag: str):
    return A(tag, href=f"/tags/{tag}", cls="tag")


def reading_time_badge(minutes: int, lang: str):
    s = UI_STRINGS[lang]
    return Span(f"{minutes} {s['reading_time']}", cls="reading-time")


def post_card(post: dict, lang: str):
    s    = UI_STRINGS[lang]
    href = f"/posts/{lang}/{post['slug']}"
    tags = [tag_badge(t) for t in post.get("tags", [])]
    return Article(
        H2(A(post["title"], href=href)),
        P(
            Span(post["date_str"], cls="post-date"),
            Span(" · "),
            reading_time_badge(post["reading_time"], lang),
            cls="post-meta",
        ),
        P(post["description"], cls="post-description") if post.get("description") else "",
        Div(*tags, cls="post-tags") if tags else "",
        A(s["read_more"], href=href, cls="read-more"),
        cls="post-card",
    )


def toc_nav(toc: list[dict], lang: str):
    if not toc:
        return ""
    s     = UI_STRINGS[lang]
    items = []
    for entry in toc:
        cls = "toc-h2" if entry["level"] == 2 else "toc-h3"
        items.append(Li(A(entry["text"], href=f"#{entry['anchor']}"), cls=cls))
    return Nav(
        P(s["toc_label"], cls="toc-label"),
        Ul(*items, cls="toc-list"),
        cls="toc-nav",
    )


def series_nav(prev_post: dict | None, next_post: dict | None, lang: str):
    s     = UI_STRINGS[lang]
    items = []
    if prev_post:
        href = f"/posts/{prev_post['lang']}/{prev_post['slug']}"
        items.append(A(f"{s['series_prev']} {prev_post['title']}", href=href, cls="series-prev"))
    if next_post:
        href = f"/posts/{next_post['lang']}/{next_post['slug']}"
        items.append(A(f"{next_post['title']} {s['series_next']}", href=href, cls="series-next"))
    if not items:
        return ""
    return Nav(*items, cls="series-nav")


def post_page_content(post: dict, lang: str):
    s         = UI_STRINGS[lang]
    back_href = "/" if lang == DEFAULT_LANG else f"/{_secondary_lang}/"
    tags      = [tag_badge(t) for t in post.get("tags", [])]
    prev_p, next_p = get_series_neighbors(post)

    show_toc = post["toc_enabled"] and len(post["toc"]) >= 3
    toc_el   = toc_nav(post["toc"], lang) if show_toc else ""

    series_label = ""
    if post["series"] and post["series_part"]:
        series_label = Span(
            f"{s['series_part']} {post['series_part']}: {post['series']}",
            cls="series-label",
        )

    return (
        Header(
            series_label,
            H1(post["title"]),
            P(
                Span(post["date_str"], cls="post-date"),
                Span(" · "),
                reading_time_badge(post["reading_time"], lang),
                cls="post-meta",
            ),
            Div(*tags, cls="post-tags") if tags else "",
            cls="post-header",
        ),
        Div(
            toc_el,
            Div(NotStr(post["content_html"]), cls="post-body"),
            cls="post-layout",
        ),
        series_nav(prev_p, next_p, lang) if (prev_p or next_p) else "",
        Div(
            A(s["back_to_blog"], href=back_href, cls="back-link"),
            cls="post-footer",
        ),
    )


def not_found_page(lang: str):
    s         = UI_STRINGS[lang]
    back_href = "/" if lang == DEFAULT_LANG else f"/{_secondary_lang}/"
    return Div(
        H1("404"),
        P(s["not_found"]),
        P(s["not_found_detail"], cls="post-meta"),
        A(s["back_to_blog"], href=back_href, cls="back-link"),
        cls="not-found",
    )


def blog_index_content(posts: list[dict], lang: str):
    s     = UI_STRINGS[lang]
    cards = [post_card(p, lang) for p in posts]
    return (
        Div(
            H1(SITE_NAME),
            P(s["subtitle"], cls="page-subtitle"),
            cls="page-header",
        ),
        Div(*cards, cls="post-list") if cards else P(s["no_posts"], cls="post-meta"),
    )


# ── RSS ───────────────────────────────────────────────────────────────────────

def _build_rss(lang: str) -> str:
    s        = UI_STRINGS[lang]
    base     = f"https://{SITE_NAME}"
    root     = Element("rss", version="2.0")
    root.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    channel  = SubElement(root, "channel")
    SubElement(channel, "title").text       = s["rss_title"]
    SubElement(channel, "link").text        = base
    SubElement(channel, "description").text = s["rss_description"]
    SubElement(channel, "language").text    = lang
    feed_path  = "/feed.xml" if lang == DEFAULT_LANG else f"/feed/{lang}.xml"
    atom_link  = SubElement(channel, "atom:link")
    atom_link.set("href", f"{base}{feed_path}")
    atom_link.set("rel",  "self")
    atom_link.set("type", "application/rss+xml")

    for post in get_all_posts(lang)[:20]:
        item = SubElement(channel, "item")
        SubElement(item, "title").text       = post["title"]
        SubElement(item, "link").text        = f"{base}/posts/{lang}/{post['slug']}"
        SubElement(item, "guid").text        = f"{base}/posts/{lang}/{post['slug']}"
        SubElement(item, "description").text = post.get("description", "")
        raw = post["date"]
        if hasattr(raw, "timetuple"):
            SubElement(item, "pubDate").text = formatdate(time.mktime(raw.timetuple()))

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="unicode")


# ── Routes — default language (es) ───────────────────────────────────────────

@app.get("/")
@app.get(f"/posts/{DEFAULT_LANG}/")
def blog_index_default(req):
    posts = get_all_posts(DEFAULT_LANG)
    return page_shell("Blog", DEFAULT_LANG, "/",
                      UI_STRINGS[DEFAULT_LANG]["subtitle"],
                      *blog_index_content(posts, DEFAULT_LANG))


@app.get(f"/posts/{DEFAULT_LANG}/{{slug}}")
def blog_post_default(req, slug: str):
    post = get_post(slug, DEFAULT_LANG)
    if not post:
        return page_shell("404", DEFAULT_LANG, f"/posts/{DEFAULT_LANG}/{slug}", "",
                          not_found_page(DEFAULT_LANG))
    return page_shell(post["title"], DEFAULT_LANG, f"/posts/{DEFAULT_LANG}/{slug}",
                      post.get("description", ""), *post_page_content(post, DEFAULT_LANG))


@app.get(f"/pages/{DEFAULT_LANG}/about")
def about_default(req):
    html = load_page(f"pages/{DEFAULT_LANG}/about.md")
    return page_shell("Sobre mí", DEFAULT_LANG, f"/pages/{DEFAULT_LANG}/about", "",
                      Div(NotStr(html), cls="about-body"))


# ── Routes — secondary language (en) ─────────────────────────────────────────

@app.get(f"/{_secondary_lang}/")
@app.get(f"/posts/{_secondary_lang}/")
def blog_index_secondary(req):
    posts = get_all_posts(_secondary_lang)
    return page_shell("Blog", _secondary_lang, f"/{_secondary_lang}/",
                      UI_STRINGS[_secondary_lang]["subtitle"],
                      *blog_index_content(posts, _secondary_lang))


@app.get(f"/posts/{_secondary_lang}/{{slug}}")
def blog_post_secondary(req, slug: str):
    post = get_post(slug, _secondary_lang)
    if not post:
        return page_shell("404", _secondary_lang, f"/posts/{_secondary_lang}/{slug}", "",
                          not_found_page(_secondary_lang))
    return page_shell(post["title"], _secondary_lang, f"/posts/{_secondary_lang}/{slug}",
                      post.get("description", ""), *post_page_content(post, _secondary_lang))


@app.get(f"/pages/{_secondary_lang}/about")
def about_secondary(req):
    html = load_page(f"pages/{_secondary_lang}/about.md")
    return page_shell("About", _secondary_lang, f"/pages/{_secondary_lang}/about", "",
                      Div(NotStr(html), cls="about-body"))


# ── Routes — Tags ─────────────────────────────────────────────────────────────

@app.get("/tags/")
def tags_index(req):
    sorted_tags = sorted(TAG_INDEX.items(), key=lambda kv: len(kv[1]), reverse=True)
    lang = DEFAULT_LANG
    s    = UI_STRINGS[lang]
    items = [
        Li(
            A(tag, href=f"/tags/{tag}", cls="tag"),
            Span(f" ({len(posts)})", cls="tag-count"),
        )
        for tag, posts in sorted_tags
    ]
    return page_shell(s["all_tags"], lang, "/tags/", "",
        Div(H1(s["all_tags"]), Ul(*items, cls="tag-cloud"), cls="tags-page")
    )


@app.get("/tags/{tag}")
def tag_view(req, tag: str):
    posts = TAG_INDEX.get(tag, [])
    lang  = DEFAULT_LANG
    s     = UI_STRINGS[lang]
    sections: list = []
    for l in SUPPORTED_LANGS:
        lang_posts = [p for p in posts if p["lang"] == l]
        if lang_posts:
            sections.append(H2(l.upper()))
            sections.extend([post_card(p, l) for p in lang_posts])
    content = Div(
        H1(f"{s['tag_posts']} #{tag}"),
        Div(*sections, cls="post-list") if sections else P(s["no_posts"], cls="post-meta"),
        cls="tags-page",
    )
    return page_shell(f"#{tag}", lang, f"/tags/{tag}", "", content)


# ── Routes — RSS ──────────────────────────────────────────────────────────────

@app.get("/feed.xml")
def rss_default(req):
    return Response(_build_rss(DEFAULT_LANG), media_type="application/rss+xml; charset=utf-8")


@app.get(f"/feed/{_secondary_lang}.xml")
def rss_secondary(req):
    return Response(_build_rss(_secondary_lang), media_type="application/rss+xml; charset=utf-8")


# ── Theme toggle ──────────────────────────────────────────────────────────────

@app.post("/set-theme")
async def set_theme(req):
    form      = await req.form()
    current   = form.get("current_theme", "dark")
    new_theme = "light" if current == "dark" else "dark"
    resp      = Response(status_code=204)
    resp.set_cookie("theme", new_theme, max_age=60 * 60 * 24 * 365, samesite="lax", path="/")
    return resp


# ── Static files ──────────────────────────────────────────────────────────────

@app.get("/static/{fname:path}")
async def static_files(fname: str):
    return FileResponse(f"static/{fname}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dev = os.environ.get("RAILWAY_ENVIRONMENT") is None
    serve(port=PORT, reload=dev)
