from .base import *  # noqa

DEBUG = True

# Allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# More verbose logging in dev
LOGGING['root']['level'] = 'DEBUG'
