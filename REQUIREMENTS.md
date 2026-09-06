# pypost — Developer Guide

A minimal, bilingual blog framework. No build step, no database.
Stack: **FastHTML** · **Mistune** · **Pygments** · **PicoCSS** · **Uvicorn**

---

## Running locally

```bash
# Install deps (uv recommended)
uv venv && uv pip install -r requirements.txt

# Start dev server (auto-reload)
uv run python main.py
# → http://localhost:8000
```

Default lang (ES) is at `/`, secondary lang (EN) at `/en/`.

---

## Project structure

```text
pypost/
├── main.py           # App: post loading, components, routes
├── config.py         # Site identity, languages, nav, UI strings
├── static/
│   ├── custom.css    # Theme (edit CSS variables to restyle)
│   └── pygments.css  # Auto-generated on startup — do not edit
├── posts/
│   ├── en/           # English posts (*.md)
│   └── es/           # Spanish posts (*.md)
├── pages/
│   ├── en/about.md
│   └── es/about.md
├── pyproject.toml
├── requirements.txt
└── Procfile          # Railway deployment
```

---

## Adding a post

1. Create `posts/{lang}/YYYYMMDD-my-slug.md`
2. Add frontmatter at the top
3. Restart the server (or it will auto-reload in dev mode).

```markdown
---
title: My Post Title
date: 2026-04-01
published: true
slug: my-post           # optional — auto-derived from title
description: "One-line summary shown on cards and in RSS."
tags: [python, demo]
series: "My Series"     # optional
series_part: 1          # required if series is set
toc: true               # default true; set false to hide ToC
---

Your content here...
```

### Frontmatter reference

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `title` | string | filename stem | Required in practice |
| `date` | date | — | `YYYY-MM-DD` format |
| `published` | bool | `false` | Must be `true` to appear |
| `slug` | string | slugified title | Must be unique per language |
| `description` | string | `""` | Cards, RSS, og:description |
| `tags` | list | `[]` | Creates tag index pages |
| `series` | string | `""` | Groups posts into a series |
| `series_part` | int | `null` | Order within the series |
| `toc` | bool | `true` | Show ToC when ≥3 headings |

---

## Adding a static page

1. Create `pages/{lang}/mypage.md`

2. Add a route in `main.py`:

```python
@app.get("/pages/en/mypage")
def mypage_en(req):
    html = load_page("pages/en/mypage.md")
    return page_shell("My Page", "en", "/pages/en/mypage", "",
                      Div(NotStr(html), cls="about-body"))
```

3. Add it to `NAV_LINKS` in `config.py`:

```python
NAV_LINKS = {
    "en": [..., ("My Page", "/pages/en/mypage")],
    "es": [..., ("Mi página", "/pages/es/mypage")],
}
```

---

## Configuring the site

Edit `config.py`:

| Variable | Description |
| --- | --- |
| `SITE_NAME` | Shown in nav, footer, title tags |
| `SITE_DESCRIPTION` | Default meta description |
| `AUTHOR` | Default post author |
| `PORT` | Dev port (overridden by `$PORT` in production) |
| `DEFAULT_LANG` | Language served at `/` |
| `SUPPORTED_LANGS` | Both languages, e.g. `["es", "en"]` |
| `NAV_LINKS` | Per-language nav items |
| `UI_STRINGS` | All button labels, messages, RSS strings |

---

## Changing the theme

All colors are CSS variables in `static/custom.css`. Edit the `:root / [data-theme="dark"]` block for dark mode and `[data-theme="light"]` for light mode.

Key variables:

| Variable | Role |
| --- | --- |
| `--bg` | Page background |
| `--bg-surface` | Card / nav background |
| `--accent` | Links, h3, tags, borders |
| `--text` | Body text |
| `--text-heading` | h1/h2 color |
| `--text-muted` | Dates, meta, muted text |
| `--code-bg` | Inline and block code background |

The `pygments.css` file (syntax highlighting) is auto-generated from Pygments styles on startup. To change highlight styles, edit these lines in `main.py`:

```python
_dark_css  = HtmlFormatter(style="monokai",  ...).get_style_defs(...)
_light_css = HtmlFormatter(style="friendly", ...).get_style_defs(...)
```

Run `python -c "from pygments.styles import get_all_styles; print(list(get_all_styles()))"` to list available styles.

---

## Series

Posts with the same `series` string are grouped. Add `series_part` (integer) to define order. pypost auto-injects prev/next navigation at the bottom of each post.

Series work across languages — part 1 can be in ES and part 2 in EN.

---

## Tags

Any value in a post's `tags` list creates:

- A tag badge on the post card and post page
- An entry on `/tags/`
- A filtered list page at `/tags/{tag}`

---

## Table of Contents

When a post has 3 or more h2/h3 headings, a sticky sidebar ToC is generated. Headings get `id` attributes automatically from their slugified text.

Set `toc: false` in frontmatter to disable for a specific post.

---

## RSS feeds

- Default lang feed: `/feed.xml`
- Secondary lang feed: `/feed/{lang}.xml` (e.g. `/feed/en.xml`)

Feeds include the 20 most recent posts. Autodiscovery `<link>` tags are injected into every page.

---

## Deploying on Railway

1. Push the repo to GitHub
2. Create a new Railway project from the repo
3. Railway detects the `Procfile` and sets `$PORT` automatically
4. No environment variables needed beyond `PORT` (set by Railway)

The `static/pygments.css` file is gitignored and regenerated at startup.
