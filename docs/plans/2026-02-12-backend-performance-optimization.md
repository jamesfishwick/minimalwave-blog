# Backend Performance Optimization

**Date:** 2026-02-12
**Status:** Approved
**Priority:** Optional Enhancement

## Context

Django application with PostgreSQL database. Site is already reasonably performant, but these optimizations will improve scalability and reduce server costs.

## Current Architecture

- **Framework:** Django 4.2+
- **Database:** PostgreSQL 14
- **Cache:** None (Django default)
- **Deployment:** Azure App Service
- **Traffic:** Low-moderate (personal blog)

## Optimization Opportunities

### 1. N+1 Query Detection & Prevention

**Problem:** Views may be making redundant database queries

**Detection:**
```python
# Install django-debug-toolbar
pip install django-debug-toolbar

# settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

**Common N+1 patterns to fix:**

**a) Blog index (entries with tags)**
```python
# BEFORE (N+1 query)
def index(request):
    entries = Entry.objects.filter(status='published')[:10]
    # Each entry.tags.all() triggers a query = 1 + N queries

# AFTER (2 queries total)
def index(request):
    entries = Entry.objects.filter(status='published').prefetch_related('tags')[:10]
```

**b) Entry detail (authors)**
```python
# BEFORE
def entry_detail(request, slug):
    entry = Entry.objects.get(slug=slug)
    # entry.authors.all() triggers query

# AFTER
def entry_detail(request, slug):
    entry = Entry.objects.select_related('user').prefetch_related('authors').get(slug=slug)
```

**c) Related posts**
```python
# blog/models.py
def get_related_posts(self, limit=5):
    # BEFORE: N queries for each tag
    tag_ids = self.tags.values_list('id', flat=True)

    # AFTER: 1 query with subquery
    return Entry.objects.filter(
        tags__in=tag_ids,
        status='published'
    ).exclude(id=self.id).distinct()[:limit]
```

**Expected improvement:**
- Index page: 11 queries → 2 queries
- Detail page: 5 queries → 2 queries
- Faster page loads, reduced DB load

---

### 2. Template Fragment Caching

**Problem:** Sidebar widgets regenerate on every request

**Implementation:**

**a) Popular posts sidebar**
```html
<!-- templates/blog/index.html -->
{% load cache %}

{% cache 300 popular_posts %}
<aside class="popular-posts">
  <h3>Popular Posts</h3>
  <ul>
    {% for post in popular_posts %}
      <li>
        <a href="{{ post.get_absolute_url }}">{{ post.title }}</a>
        <span class="view-count">{{ post.view_count }} views</span>
      </li>
    {% endfor %}
  </ul>
</aside>
{% endcache %}
```

**b) Tag cloud**
```html
{% cache 600 tag_cloud %}
<div class="tag-cloud">
  {% for tag in tags %}
    <a href="{% url 'blog:tag' tag.slug %}" class="tag">{{ tag.name }}</a>
  {% endfor %}
</div>
{% endcache %}
```

**c) Recent posts**
```html
{% cache 120 recent_posts %}
<aside class="recent-posts">
  {% for post in recent_posts %}
    <!-- ... -->
  {% endfor %}
</aside>
{% endcache %}
```

**Expected improvement:**
- Sidebar renders from cache (no DB queries)
- Cache invalidates every 5-10 minutes
- Faster page loads for repeat visitors

---

### 3. Redis Cache Backend

**Problem:** Django default cache is in-memory (single process)

**Implementation:**

**a) Install Redis**
```bash
# Local development
docker-compose.yml:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

# Azure production
# Use Azure Cache for Redis (Basic tier ~$15/month)
```

**b) Configure Django**
```python
# settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'minimalwave',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Session storage in Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

**c) Cache expensive queries**
```python
# blog/views.py
from django.core.cache import cache

def get_popular_posts(limit=5, days=30):
    cache_key = f'popular_posts_{limit}_{days}'
    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    # Expensive query
    popular = PageView.objects.filter(
        viewed_date__gte=timezone.now().date() - timedelta(days=days)
    ).values('object_id').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:limit]

    # Cache for 10 minutes
    cache.set(cache_key, popular, 600)
    return popular
```

**Expected improvement:**
- Shared cache across multiple app instances
- Faster session lookups
- Persistent cache (survives restarts)
- Reduced database load

---

### 4. Database Connection Pooling

**Problem:** Opening new DB connection on every request is slow

**Implementation:**

**a) Install pgbouncer (production)**
```dockerfile
# Dockerfile.pgbouncer
FROM edoburu/pgbouncer:latest
COPY pgbouncer.ini /etc/pgbouncer/
```

```ini
# pgbouncer.ini
[databases]
minimalwave = host=your-postgres.postgres.database.azure.com port=5432 dbname=minimalwave

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
```

**b) Django configuration**
```python
# settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'pgbouncer',  # Instead of direct Postgres
        'PORT': '6432',
        'NAME': 'minimalwave',
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'CONN_MAX_AGE': 600,  # Connection persists for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}
```

**Alternative (simpler - Azure built-in pooling):**
```python
# Azure PostgreSQL already has connection pooling
# Just enable persistent connections:
DATABASES['default']['CONN_MAX_AGE'] = 600
```

**Expected improvement:**
- Reused connections (no TCP handshake overhead)
- Better performance under concurrent load
- Reduced DB connection overhead

---

### 5. Query Optimization (Indexes)

**Problem:** Slow queries on common filters

**Add database indexes:**
```python
# blog/models.py
class Entry(BaseEntry):
    class Meta:
        indexes = [
            models.Index(fields=['status', '-created']),  # Index for published posts
            models.Index(fields=['slug']),  # Slug lookups
            models.Index(fields=['created']),  # Date archives
        ]

class PageView(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),  # View count queries
            models.Index(fields=['viewed_date']),  # Date filtering
            models.Index(fields=['visitor_hash', 'viewed_date']),  # Deduplication
        ]
```

**Migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Analyze slow queries:**
```python
# settings/development.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',  # Log all SQL queries
        },
    },
}

# Check EXPLAIN output
from django.db import connection
print(connection.queries)  # After view execution
```

**Expected improvement:**
- Faster tag filtering
- Faster date archive queries
- Faster view count aggregations

---

### 6. Middleware Optimization

**Problem:** Middleware runs on every request (even static files)

**Optimize middleware order:**
```python
# settings/base.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static early
    'django.middleware.cache.UpdateCacheMiddleware',  # Cache middleware (top)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'blog.middleware.ViewCountMiddleware',  # Custom middleware last
    'django.middleware.cache.FetchFromCacheMiddleware',  # Cache middleware (bottom)
]
```

**Skip middleware for static files:**
```python
# ViewCountMiddleware
def process_request(self, request):
    # Skip middleware for static files
    if request.path.startswith('/static/') or request.path.startswith('/media/'):
        return None
```

---

## Implementation Checklist

### Phase 1: Quick Wins (No Infrastructure)
- [ ] Install django-debug-toolbar
- [ ] Audit views for N+1 queries
- [ ] Add `select_related()` and `prefetch_related()`
- [ ] Add database indexes
- [ ] Enable `CONN_MAX_AGE` for persistent connections
- [ ] Add template fragment caching
- [ ] Optimize middleware order

### Phase 2: Redis Integration
- [ ] Set up Redis (Docker for dev, Azure for prod)
- [ ] Configure Django cache backend
- [ ] Move sessions to Redis
- [ ] Cache expensive queries
- [ ] Test cache invalidation

### Phase 3: Advanced Optimizations
- [ ] Set up pgbouncer (if needed)
- [ ] Database query profiling
- [ ] Slow query logging
- [ ] APM monitoring (optional: New Relic, Datadog)

## Performance Targets

**Current (estimated):**
- Response time: 100-300ms
- Database queries per page: 5-15
- Cache hit rate: 0% (no cache)

**Target (post-optimization):**
- Response time: 30-80ms
- Database queries per page: 1-3
- Cache hit rate: 70-90%

## Cost Implications

- **Redis (Azure Cache):** $15-50/month (Basic/Standard tier)
- **pgbouncer:** Free (self-hosted) or included in Azure Postgres
- **No additional costs** for Phases 1 & 3

## Dependencies

```txt
# requirements.txt additions
django-redis>=5.4.0  # Redis cache backend
django-debug-toolbar>=4.2.0  # Development only
```

## Monitoring

Track these metrics before/after optimization:

- Average response time (Azure Application Insights)
- Database query count (django-debug-toolbar)
- Cache hit rate (Redis INFO stats)
- Error rate (Azure metrics)

## Notes

- Start with Phase 1 (free, immediate impact)
- Phase 2 (Redis) adds infrastructure cost but major performance win
- Phase 3 only needed if traffic grows significantly
- Azure PostgreSQL has built-in connection pooling (may not need pgbouncer)
