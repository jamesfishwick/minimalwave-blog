# Production settings

import logging

from .base import *

DEBUG = False

# Configure logging to track Azure storage issues
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Cache settings
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv(
            "REDIS_URL", "redis://minimalwave-cache.redis.cache.windows.net:6379/0"
        ),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.getenv("REDIS_PASSWORD", ""),
        },
    }
}

# Cache configuration
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = "minimalwave"

# Static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = False  # Should be False in production
# Strict: a {% static %} name missing from the manifest fails loudly at deploy
# rather than silently serving an unhashed, 404-ing URL under manifest storage.
WHITENOISE_MANIFEST_STRICT = True
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "zip",
    "gz",
    "tgz",
    "bz2",
    "tbz",
    "xz",
    "br",
]
WHITENOISE_MIMETYPES = {
    ".css": "text/css",
    ".js": "application/javascript",
}

# Azure Blob Storage for media files
AZURE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_CONTAINER = "media"

logger.info("========== Azure Storage Configuration ==========")
logger.info(f"AZURE_ACCOUNT_NAME from env: {AZURE_ACCOUNT_NAME}")
logger.info(f"AZURE_ACCOUNT_KEY present: {bool(AZURE_ACCOUNT_KEY)}")
logger.info(f"AZURE_CONTAINER: {AZURE_CONTAINER}")

if AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY:
    # Use Azure Blob Storage in production (Django 4.2+ STORAGES format)
    logger.info("✅ Azure credentials found - configuring Azure Blob Storage")

    # Django 5.2 requires STORAGES configuration instead of DEFAULT_FILE_STORAGE
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.azure_storage.AzureStorage",
            "OPTIONS": {
                "account_name": AZURE_ACCOUNT_NAME,
                "account_key": AZURE_ACCOUNT_KEY,
                "azure_container": AZURE_CONTAINER,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"
    MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/"

    logger.info("STORAGES backend: storages.backends.azure_storage.AzureStorage")
    logger.info(f"MEDIA_URL: {MEDIA_URL}")
    logger.info(f"Azure account: {AZURE_ACCOUNT_NAME}")
    logger.info(f"Azure container: {AZURE_CONTAINER}")
    logger.info("================================================")
else:
    # Fallback to local storage (development/testing)
    logger.warning("⚠️  Azure credentials NOT found - using local storage")
    logger.warning(f"AZURE_ACCOUNT_NAME: {AZURE_ACCOUNT_NAME}")
    logger.warning(f"AZURE_ACCOUNT_KEY present: {bool(AZURE_ACCOUNT_KEY)}")
    logger.info("================================================")

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Database
# Use dj-database-url to parse DATABASE_URL if available
import dj_database_url

db_from_env = dj_database_url.config(conn_max_age=600)

if db_from_env:
    DATABASES = {"default": db_from_env}
    # Add SSL options
    DATABASES["default"]["OPTIONS"] = {
        "sslmode": "require",
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
else:
    # Fallback to explicit configuration
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "minimalwave"),
            "USER": os.getenv("DB_USER", "minimalwave"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv(
                "DB_HOST", "minimalwave-blog-db-2025.postgres.database.azure.com"
            ),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": 600,  # Connection pooling: Keep connections alive for 10 minutes
            "OPTIONS": {
                "sslmode": "require",
                "keepalives": 1,
                "keepalives_idle": 60,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            },
        }
    }

# Security - Disable SSL redirect for Azure App Service
SECURE_SSL_REDIRECT = False  # Azure handles SSL termination
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Additional security headers flagged by Lighthouse best-practices
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

# Content Security Policy (django-csp 4.x)
# The two inline <script> blocks in base.html are matched by sha256 hash, not a
# nonce: this site whole-site-caches rendered HTML, and a per-request nonce baked
# into a cached body can never match the header nonce on a cache hit. Hashes are
# stable across cached copies. If either inline script changes, recompute its
# hash (base64 sha256 of the exact bytes between <script> and </script>).
# style-src keeps 'unsafe-inline' because markdown image shortcodes emit style="".
from urllib.parse import urlparse

from csp.constants import NONE, SELF

# base.html:77 theme flash-prevention, and the theme-toggle script at the body end.
_THEME_INIT_HASH = "'sha256-7vcU3qHxNjFgsBltLUeqjnsJNDqy4KVYXFL7hc5PIQU='"
_THEME_TOGGLE_HASH = "'sha256-/5QwnhIk/hdiNnu3RLhGbdavjOnS4p7GstEPTYvxx70='"

# Only trust the Plausible origin when the script URL is absolute; a self-hosted
# proxy uses a same-origin path (already covered by SELF), and an empty/relative
# value would otherwise emit the malformed CSP token "://".
_parsed_plausible = urlparse(PLAUSIBLE_SCRIPT_URL)
if _parsed_plausible.scheme and _parsed_plausible.netloc:
    _plausible_src = [f"{_parsed_plausible.scheme}://{_parsed_plausible.netloc}"]
else:
    _plausible_src = []

# self + data: + the Azure blob host + any https origin, because published posts
# can embed externally hosted images via the {{img:https://...}} shortcode.
_img_src = [SELF, "data:", "https:"]
if AZURE_ACCOUNT_NAME:
    _img_src.append(f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net")

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF, _THEME_INIT_HASH, _THEME_TOGGLE_HASH, *_plausible_src],
        "style-src": [SELF, "'unsafe-inline'"],
        "img-src": _img_src,
        "connect-src": [SELF, *_plausible_src],
        "font-src": [SELF],
        "base-uri": [SELF],
        "object-src": [NONE],
        "frame-ancestors": [NONE],
    }
}

# Middleware - Add cache and compression while preserving base middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "minimalwave-blog.middleware.CacheControlMiddleware",
]

# Override logging for production - use console only
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
