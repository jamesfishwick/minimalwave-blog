from django.db import models
from django.utils import timezone


class EnhancedTag(models.Model):
    """Simple tag model for organizing content"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, help_text="Brief description of this tag")

    # Optional display fields (kept for future use if needed)
    is_featured = models.BooleanField(default=False, help_text="Show this tag prominently")
    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        ordering = ['name']
        # Indexes removed to avoid migration conflicts across Django versions
        # The slug field has unique=True which creates an index automatically
        # Additional indexes can be added via raw SQL if needed for performance

    def __str__(self):
        return self.name

    def usage_count(self):
        """Calculate usage across all content types"""
        from blog.models import Entry, Blogmark
        from til.models import TIL

        count = 0
        count += Entry.objects.filter(tags=self).count()
        count += Blogmark.objects.filter(tags=self).count()
        count += TIL.objects.filter(tags=self).count()
        return count


