---
title: "Features Demo: Code, ToC & Series"
date: 2026-03-25
published: true
slug: features-demo
description: "Demonstrates syntax highlighting, Table of Contents, and series navigation."
tags: [demo, python]
series: "Getting Started"
series_part: 1
toc: true
---

This post demonstrates the three advanced features of pypost: **server-side syntax highlighting**, **auto-generated Table of Contents**, and **series navigation**.

## Syntax Highlighting

Code blocks are highlighted server-side by [Pygments](https://pygments.org) — no JavaScript required. Just fence your code with a language tag.

```python
def load_posts(lang: str) -> list[dict]:
    base = Path("posts") / lang
    posts = []
    for path in base.glob("*.md"):
        post = fm.load(str(path))
        if not post.get("published", False):
            continue
        posts.append({"slug": post["slug"], "title": post["title"]})
    return sorted(posts, key=lambda p: p["date"], reverse=True)
```

Multiple languages are supported:

```bash
uv run python main.py
# Starts on http://localhost:8000
```

```yaml
title: My Post
date: 2026-03-25
published: true
tags: [python, demo]
```

## Table of Contents

When a post has **3 or more h2/h3 headings**, a sticky ToC sidebar is generated automatically. You're reading one right now. Set `toc: false` in frontmatter to disable it for a specific post.

### ToC behaviour

- h2 headings become top-level ToC entries
- h3 headings are indented below their parent h2
- The sidebar sticks to the viewport on desktop
- On mobile it collapses to a flat block above the content

## Series Navigation

Posts in the same series are linked with prev/next navigation. Set `series` and `series_part` in frontmatter:

```yaml
series: "Getting Started"
series_part: 1
```

The nav bar at the bottom of this page shows a "Next →" link pointing to part 2 (if it exists). This works across languages — parts can be in different languages within the same series.

### Adding more parts

Create a new post with the same `series` value and the next `series_part` number. pypost builds the series index at startup and injects the navigation automatically.
