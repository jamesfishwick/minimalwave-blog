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


class ContentLinkedIn(models.Model):
    """Separate model for LinkedIn integration - can be linked to any content"""
    CONTENT_TYPE_CHOICES = [
        ('entry', 'Blog Entry'),
        ('blogmark', 'Blogmark'),
        ('til', 'TIL'),
    ]

    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.IntegerField()

    # LinkedIn settings
    enabled = models.BooleanField(
        default=False,
        help_text="Automatically post to LinkedIn when published"
    )
    custom_text = models.TextField(
        blank=True,
        null=True,
        help_text="Custom text for LinkedIn post (leave blank to use default)"
    )

    # Status tracking
    posted = models.BooleanField(
        default=False,
        help_text="Whether this content has been posted to LinkedIn"
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    post_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="LinkedIn post ID for reference"
    )
    post_url = models.URLField(blank=True, help_text="URL to the LinkedIn post")

    # Error handling
    last_error = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        unique_together = ['content_type', 'content_id']
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['posted', 'enabled']),
        ]

    def __str__(self):
        return f"LinkedIn config for {self.content_type} #{self.content_id}"

    def get_content(self):
        """Get the associated content object"""
        if self.content_type == 'entry':
            from blog.models import Entry
            return Entry.objects.get(pk=self.content_id)
        elif self.content_type == 'blogmark':
            from blog.models import Blogmark
            return Blogmark.objects.get(pk=self.content_id)
        elif self.content_type == 'til':
            from til.models import TIL
            return TIL.objects.get(pk=self.content_id)
        return None