import os

# ── Site identity ─────────────────────────────────────────────────────────────
SITE_NAME        = "pypost"
SITE_DESCRIPTION = "A blog built with pypost."
AUTHOR           = "author"
PORT             = int(os.environ.get("PORT", 8000))
SITE_URL         = os.environ.get("SITE_URL", f"http://localhost:{PORT}")

# ── Language ──────────────────────────────────────────────────────────────────
DEFAULT_LANG    = "es"          # serves at /  (other lang at /en/)
SUPPORTED_LANGS = ["es", "en"]

# ── Navigation links per language ─────────────────────────────────────────────
NAV_LINKS = {
    "es": [("Blog", "/"), ("Temas", "/tags/"), ("Sobre mí", "/pages/es/about")],
    "en": [("Blog", "/en/"), ("Topics", "/tags/"), ("About", "/pages/en/about")],
}

# ── UI strings ────────────────────────────────────────────────────────────────
UI_STRINGS = {
    "es": {
        "read_more":      "Leer →",
        "back_to_blog":   "← Volver",
        "toggle_theme":   "☀ / ☾",
        "switch_lang":    "English",
        "not_found":      "Página no encontrada.",
        "not_found_detail": "Este artículo no existe o fue movido.",
        "reading_time":   "min de lectura",
        "all_tags":       "Todos los temas",
        "no_posts":       "Sin publicaciones aún.",
        "series_prev":    "← Anterior",
        "series_next":    "Siguiente →",
        "series_part":    "Parte",
        "toc_label":      "En este artículo",
        "tag_posts":      "Artículos sobre",
        "subtitle":       "Publicaciones recientes.",
        "footer":         SITE_NAME,
        "rss_title":      f"{SITE_NAME} — Blog",
        "rss_description": SITE_DESCRIPTION,
    },
    "en": {
        "read_more":      "Read →",
        "back_to_blog":   "← Back",
        "toggle_theme":   "☀ / ☾",
        "switch_lang":    "Español",
        "not_found":      "Page not found.",
        "not_found_detail": "This post does not exist or was moved.",
        "reading_time":   "min read",
        "all_tags":       "All topics",
        "no_posts":       "No posts yet.",
        "series_prev":    "← Previous",
        "series_next":    "Next →",
        "series_part":    "Part",
        "toc_label":      "In this article",
        "tag_posts":      "Posts tagged",
        "subtitle":       "Recent posts.",
        "footer":         SITE_NAME,
        "rss_title":      f"{SITE_NAME} — Blog",
        "rss_description": SITE_DESCRIPTION,
    },
}
