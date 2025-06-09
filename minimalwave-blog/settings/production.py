# Production settings

from minimalwave_blog.settings.base import *

DEBUG = False

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://minimalwave-cache.redis.cache.windows.net:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.getenv('REDIS_PASSWORD', ''),
        }
    }
}

# Cache configuration
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'minimalwave'

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Database
# Use dj-database-url to parse DATABASE_URL if available
import dj_database_url
db_from_env = dj_database_url.config(conn_max_age=600)

if db_from_env:
    DATABASES = {
        'default': db_from_env
    }
    # Add SSL options
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
        'keepalives': 1,
        'keepalives_idle': 60,
        'keepalives_interval': 10,
        'keepalives_count': 5,
    }
else:
    # Fallback to explicit configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'minimalwave'),
            'USER': os.getenv('DB_USER', 'minimalwave'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'minimalwave-blog-db-2025.postgres.database.azure.com'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,  # Connection pooling: Keep connections alive for 10 minutes
            'OPTIONS': {
                'sslmode': 'require',
                'keepalives': 1,
                'keepalives_idle': 60,
                'keepalives_interval': 10,
                'keepalives_count': 5,
            }
        }
    }

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Middleware - Add cache and compression
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'minimalwave_blog.middleware.CacheControlMiddleware',
] + MIDDLEWARE
