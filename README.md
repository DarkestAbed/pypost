# pypost

A minimal, bilingual blog engine. No build step, no database, no JavaScript
frameworks — just Markdown files and a single Python app.

**Stack:** [FastHTML](https://fastht.ml) · [Mistune](https://mistune.lepture.com) ·
[Pygments](https://pygments.org) · [PicoCSS](https://picocss.com) · [Uvicorn](https://uvicorn.org)

```bash
cd template
uv sync --group dev
uv run python main.py
# → http://localhost:8000  (ES) · /en/  (EN)
```

## Start your own blog

pypost is a [Copier](https://copier.readthedocs.io) template — no forking, no
find-and-replace:

```bash
uvx copier copy --trust gh:darkestabed/pypost my-blog
cd my-blog
```

You'll be asked for your site name, author, languages (ES/EN, either or both),
production URL, demo content, and license. A ready-to-run repo comes out the
other end — git initialized, dependencies synced, tests passing. Prefer a
one-liner?

```bash
curl -sSL https://raw.githubusercontent.com/darkestabed/pypost/main/new.sh | sh -s my-blog
```

**Stay current:** as pypost gets fixes and features, run
`uvx copier update --trust` inside your blog to re-apply the template as a diff
on top of your saved answers. Your `config.py`, content, and styles stay yours.

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
| [`template/HOWTO.md`](template/HOWTO.md) | Start here — customize your generated blog, step by step |
| [`template/REQUIREMENTS.md`](template/REQUIREMENTS.md) | Reference — every frontmatter field, config variable, and deployment note |

## Repository layout

```text
copier.yml         Questions, exclusions, and tasks for generation
new.sh             One-liner wrapper: curl | sh → copier copy
template/          Everything that ships to a generated blog
  main.py            The whole app (~800 lines): loading, components, routes
  config.py          Site identity, languages, navigation, UI strings
  config.py.jinja    Rendered into the instance's config.py from the answers
  posts/{lang}/      Blog posts — Markdown + YAML frontmatter
  pages/{lang}/      Static pages, auto-served at /pages/{lang}/{slug}
  static/            Self-hosted CSS, fonts, favicon (no CDN)
  tests/test_app.py  Config-driven route, feed, header, and security tests
  Procfile           Railway deployment
```

Copier's `_subdirectory: template` setting makes the split explicit: the repo
root holds the template *tooling*; a generated blog contains only what lives in
`template/`. Inside `template/`, `*.jinja` files are rendered at generation
time — everything else ships verbatim. To hack on the engine, work inside
`template/` — it's a fully runnable blog on its own.

## Deploy

Generated blogs deploy like any uvicorn app (Railway-ready via `Procfile`) —
see the generated README. This repo is a template and is not deployed itself.

## License

Copyright © 2026 Darkest Abed.

This project is licensed under the
[GNU AGPL-3.0-or-later](LICENSE) — free, copyleft software. If you run a
modified version on a public server, you must make its source available to
its users.