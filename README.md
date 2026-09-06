# pypost

A minimal, bilingual blog engine. No build step, no database, no JavaScript
frameworks — just Markdown files and a single Python app.

**Stack:** [FastHTML](https://fastht.ml) · [Mistune](https://mistune.lepture.com) ·
[Pygments](https://pygments.org) · [PicoCSS](https://picocss.com) · [Uvicorn](https://uvicorn.org)

```bash
uv sync --group dev
uv run python main.py
# → http://localhost:8000  (ES) · /en/  (EN)
```

## Features

- **Bilingual by design** — ES at `/`, EN at `/en/`, one nav toggle between
  them; post translations declared in a single frontmatter line
- **Zero client-side bloat** — server-rendered pages, one small inline script
  for the theme; all assets self-hosted (no CDN requests leave your site)
- **Dark/light theme** persisted in a cookie, applied server-side — no flash
- **Markdown with code highlighting** (Pygments, server-side), auto Table of
  Contents, reading time, copy-to-clipboard buttons
- **Series** with prev/next navigation, working across languages
- **Tags** with URL-safe slugs shared between languages
- **SEO ready** — sitemap, robots.txt, hreflang alternates, Open Graph/Twitter
  cards, per-language RSS feeds with full content
- **Secure defaults** — strict CSP, path-traversal regression tests, raw HTML
  in posts escaped by design
- **Scales** — index pagination, N-language route generation, data-driven
  static pages (drop a `.md`, get a route)
- **Tested** — 27 pytest tests + pyflakes, wired to GitHub Actions

## Documentation

| Doc | What's in it |
|---|---|
| [`HOWTO.md`](HOWTO.md) | Start here — turn this template into your blog, step by step |
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | Reference — every frontmatter field, config variable, and deployment note |

## Quick tour of the repo

```text
main.py            The whole app (~800 lines): loading, components, routes
config.py          Site identity, languages, navigation, UI strings
posts/{lang}/      Blog posts — Markdown + YAML frontmatter
pages/{lang}/      Static pages, auto-served at /pages/{lang}/{slug}
static/            Self-hosted CSS, fonts, favicon (no CDN)
tests/test_app.py  Route, feed, header, and security regression tests
Procfile           Railway deployment
```

## Deploy

Railway (or any uvicorn host):

```bash
uv sync
SITE_URL=https://your.blog uv run uvicorn main:app --host 0.0.0.0 --port $PORT
```

See [`HOWTO.md`](HOWTO.md) for the full customization walkthrough — colors,
fonts, a third language, highlight themes, and more.

## License

Copyright © 2026 Darkest Abed.

This project is licensed under the
[GNU AGPL-3.0-or-later](LICENSE) — free, copyleft software. If you run a
modified version on a public server, you must make its source available to
its users.