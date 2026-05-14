"""Centralized cache keys and TTLs for Alanaatii backend."""

# ─── Cache Keys ───────────────────────────────────────────────────────────────

# Catalog
CATALOG_ALL = "catalog__all"
CATALOG_CAT = "catalog__{category}"       # use .format(category=...) when needed

# Content
PUBLIC_REVIEWS = "public_reviews"
PUBLIC_FAQS    = "public_faqs"
SITE_STEPS     = "site_content_steps"

# ─── TTLs (seconds) ───────────────────────────────────────────────────────────

CATALOG_TTL = 60 * 15   # 15 minutes — changes only when admin edits catalog
REVIEWS_TTL = 60 * 10   # 10 minutes — changes when admin approves/rejects a review
FAQS_TTL    = 60 * 30   # 30 minutes — changes rarely
STEPS_TTL   = 60 * 60   # 60 minutes — homepage "how it works" steps, changes very rarely

# ─── All catalog category codes (for bulk invalidation) ──────────────────────
CATALOG_CATEGORIES = ["paper", "box", "gift", "style", "package", "letter_theme"]
