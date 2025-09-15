"""
CI-specific Django settings for GitHub Actions testing
"""
from .base import *

# Use in-memory SQLite for CI testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable debug for CI
DEBUG = False

# Simple cache for CI
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
        },
    }
}

# Use local time for tests
USE_TZ = True

# Disable migrations for faster testing
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

# Keep migrations enabled since we're testing them
# MIGRATION_MODULES = DisableMigrations()

# Simple secret key for CI
SECRET_KEY = 'ci-test-key-not-for-production'