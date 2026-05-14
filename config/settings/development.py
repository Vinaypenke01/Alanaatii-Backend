from .base import *  # noqa

DEBUG = True

# Allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# More verbose logging in dev
LOGGING['root']['level'] = 'DEBUG'

# ─── Cache: in-process memory (dev only) ─────────────────────────────────────
# Safe for single-process dev server. Resets on every restart.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "alanaatii-cache-dev",
    }
}
