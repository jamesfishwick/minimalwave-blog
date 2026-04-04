# View Count System Design

**Date:** 2026-02-12
**Status:** Approved
**Type:** Reader Engagement - Passive Analytics

## Context

Personal publishing platform (sole author, visitors read content). Need low-maintenance reader engagement features that require zero moderation.

**Selected approach:** Passive engagement with view counts
**Future enhancements:** Webmentions (auto-discover links), reading analytics, curated engagement options

## Goals

1. Track page views for blog posts, TILs, and blogmarks
2. Display view counts to readers (social proof, discover popular content)
3. Deduplicate views (unique visitors per day)
4. Zero infrastructure additions (PostgreSQL only)
5. Privacy-friendly (hash IPs, no raw storage)

## Architecture

### Database Schema

New model: `PageView` (in blog app or new analytics app)

```python
# blog/models.py or analytics/models.py
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
import hashlib

class PageView(models.Model):
    """Track page views with daily unique visitor deduplication"""

    # Generic relation to any content (Entry, Blogmark, TIL)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Deduplication fields
    visitor_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA256 hash of IP + User-Agent for privacy"
    )
    viewed_date = models.DateField(
        auto_now_add=True,
        db_index=True,
        help_text="Date of view (for unique per day counting)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('content_type', 'object_id', 'visitor_hash', 'viewed_date')]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['viewed_date']),
        ]
        ordering = ['-created_at']

    @staticmethod
    def hash_visitor(ip_address, user_agent):
        """Create privacy-preserving visitor hash"""
        data = f"{ip_address}:{user_agent}".encode('utf-8')
        return hashlib.sha256(data).hexdigest()
```

**Design rationale:**
- `GenericForeignKey` supports Entry, Blogmark, TIL models without separate tables
- `visitor_hash` = SHA256(IP + User-Agent) for privacy compliance
- `unique_together` constraint prevents duplicate views same day
- Indexes optimize view count queries
- `viewed_date` (not datetime) enables "unique per day" logic

### View Counting Logic

Middleware to track views on GET requests:

```python
# blog/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib.contenttypes.models import ContentType
from .models import PageView, Entry, Blogmark
from til.models import TIL

class ViewCountMiddleware(MiddlewareMixin):
    """Track page views with daily deduplication"""

    TRACKABLE_MODELS = {
        'blog:entry': Entry,
        'blog:blogmark': Blogmark,
        'til:detail': TIL,
    }

    def process_response(self, request, response):
        # Only track successful GET requests for published content
        if request.method != 'GET' or response.status_code != 200:
            return response

        # Check if this is a trackable view
        resolver_match = request.resolver_match
        if not resolver_match or resolver_match.view_name not in self.TRACKABLE_MODELS:
            return response

        # Get the content object
        model_class = self.TRACKABLE_MODELS[resolver_match.view_name]
        try:
            obj = model_class.objects.get(pk=resolver_match.kwargs.get('pk'))
            if obj.status != 'published':  # Only track published content
                return response
        except model_class.DoesNotExist:
            return response

        # Create visitor hash
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]
        visitor_hash = PageView.hash_visitor(ip_address, user_agent)

        # Record view (unique constraint prevents duplicates)
        content_type = ContentType.objects.get_for_model(obj)
        PageView.objects.get_or_create(
            content_type=content_type,
            object_id=obj.id,
            visitor_hash=visitor_hash,
            viewed_date=timezone.now().date()
        )

        return response

    def get_client_ip(self, request):
        """Extract client IP, handling proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

### Displaying View Counts

Add methods to content models:

```python
# blog/models.py (Entry and Blogmark), til/models.py (TIL)
from django.contrib.contenttypes.models import ContentType

class Entry(BaseEntry):
    # ... existing fields ...

    @property
    def view_count(self):
        """Total views (all time)"""
        content_type = ContentType.objects.get_for_model(self)
        return PageView.objects.filter(
            content_type=content_type,
            object_id=self.id
        ).count()

    @property
    def unique_visitors(self):
        """Unique visitors (all time)"""
        content_type = ContentType.objects.get_for_model(self)
        return PageView.objects.filter(
            content_type=content_type,
            object_id=self.id
        ).values('visitor_hash').distinct().count()

    @property
    def views_last_30_days(self):
        """Views in last 30 days"""
        from django.utils import timezone
        from datetime import timedelta

        content_type = ContentType.objects.get_for_model(self)
        cutoff_date = timezone.now().date() - timedelta(days=30)
        return PageView.objects.filter(
            content_type=content_type,
            object_id=self.id,
            viewed_date__gte=cutoff_date
        ).count()
```

## Template Integration

### Post Detail Pages

```html
<!-- templates/blog/entry.html, til/detail.html -->
<div class="post-meta">
  <time datetime="{{ entry.created|date:'Y-m-d' }}">{{ entry.created|date:"F j, Y" }}</time>
  {% if entry.view_count > 0 %}
    <span class="view-count" title="{{ entry.unique_visitors }} unique visitors">
      {{ entry.view_count }} views
    </span>
  {% endif %}
</div>
```

### Index Pages (Popular Posts Sidebar)

```html
<!-- templates/base.html or blog/index.html -->
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
```

## CSS Styling

```css
/* static/css/additional.css */
.view-count {
  display: inline-block;
  margin-left: var(--spacing-sm);
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-family: var(--font-sans);
  font-variant-numeric: tabular-nums;
}

.view-count::before {
  content: "👁️ ";  /* Or use icon font */
  opacity: 0.6;
}

.popular-posts {
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md);
  background: var(--purple-alpha-05);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.popular-posts h3 {
  color: var(--accent-color);
  margin-bottom: var(--spacing-md);
}

.popular-posts ul {
  list-style: none;
  padding: 0;
}

.popular-posts li {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) 0;
  border-bottom: 1px solid var(--border-color);
}

.popular-posts li:last-child {
  border-bottom: none;
}

.popular-posts .view-count {
  margin-left: auto;
  font-size: 0.85rem;
}
```

## Views for Popular Content

```python
# blog/views.py
def get_popular_posts(limit=5, days=30):
    """Get most viewed posts in last N days"""
    from datetime import timedelta
    from django.utils import timezone
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Count

    cutoff_date = timezone.now().date() - timedelta(days=days)
    entry_type = ContentType.objects.get_for_model(Entry)

    # Get top viewed entries
    popular_view_data = PageView.objects.filter(
        content_type=entry_type,
        viewed_date__gte=cutoff_date
    ).values('object_id').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:limit]

    # Fetch Entry objects
    entry_ids = [item['object_id'] for item in popular_view_data]
    entries = Entry.objects.filter(id__in=entry_ids, status='published')

    # Preserve order from view counts
    entry_dict = {e.id: e for e in entries}
    return [entry_dict[item['object_id']] for item in popular_view_data if item['object_id'] in entry_dict]

# In index view:
def index(request):
    # ... existing code ...
    context['popular_posts'] = get_popular_posts(limit=5, days=30)
    return render(request, 'blog/index.html', context)
```

## Admin Interface

```python
# blog/admin.py
from django.contrib import admin
from .models import PageView

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['content_object', 'viewed_date', 'created_at']
    list_filter = ['viewed_date', 'content_type']
    search_fields = ['visitor_hash']
    readonly_fields = ['content_type', 'object_id', 'visitor_hash', 'viewed_date', 'created_at']

    def has_add_permission(self, request):
        return False  # Views are auto-created by middleware

    def has_change_permission(self, request, obj=None):
        return False  # Views are immutable
```

## Implementation Checklist

1. Create `PageView` model with migrations
2. Implement `ViewCountMiddleware`
3. Add middleware to `MIDDLEWARE` setting
4. Add view count properties to Entry, Blogmark, TIL models
5. Update templates to display view counts
6. Add CSS styling for view counts
7. Implement `get_popular_posts()` helper
8. Update index views to include popular posts
9. Add PageView to Django admin
10. Test view counting (check deduplication works)
11. Performance test (add database indexes if needed)

## Privacy & Compliance

- **GDPR:** Visitor hashes are pseudonymized (SHA256), not personally identifiable
- **No cookies required:** Session-based counting uses server-side hashing
- **Data retention:** Consider adding periodic cleanup (delete views >1 year old)
- **Opt-out:** Could add `/do-not-track` header detection if needed

## Performance Considerations

- Middleware adds one DB write per unique visitor per day
- View count queries use indexed fields (fast reads)
- Popular posts query cached in template context (no N+1 problem)
- Consider adding Django cache for view counts if traffic grows

## Future Enhancements (Noted)

### Phase 2: Webmentions
- Auto-discover who's linking to posts
- Manual or semi-automated approval workflow
- Display mentions below posts

### Phase 3: Reading Analytics
- Track reading time (scroll depth)
- Trending topics dashboard
- Reader demographics (anonymized)

### Phase 4: Curated Engagement
- Manual "Responses" section (curate external replies)
- GitHub Discussions integration
- Optional: Simple reaction system (no text comments)

## Notes from Brainstorming

- Use case: Personal publishing platform (sole author)
- Zero moderation overhead required
- PostgreSQL only (no Redis/external services)
- Unique visitors per day (cookie-based deduplication)
- Skip webmentions for initial implementation (YAGNI)
