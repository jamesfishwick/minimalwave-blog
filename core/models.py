from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Category(models.Model):
    """High-level category for organizing content"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Hex color code for UI styling (e.g., #FF5733)"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon class name (e.g., 'fas fa-code')"
    )
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class EnhancedTag(models.Model):
    """Enhanced tag model with metadata and analytics"""
    CONTENT_TYPE_CHOICES = [
        ('blog', 'Blog'),
        ('til', 'TIL'),
        ('all', 'All Content'),
    ]

    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, help_text="Brief description of this tag")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tags'
    )
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        default='all',
        help_text="Which type of content this tag applies to"
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Hex color code for UI styling (e.g., #FF5733)"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon class name (e.g., 'fas fa-tag')"
    )

    # Analytics fields
    usage_count = models.IntegerField(default=0, help_text="Number of times this tag is used")
    last_used = models.DateTimeField(null=True, blank=True, help_text="Last time this tag was used")

    # Meta fields
    is_featured = models.BooleanField(default=False, help_text="Show this tag prominently")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['content_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.content_type})"

    def update_usage(self):
        """Update usage statistics for this tag"""
        from blog.models import Entry, Blogmark
        from til.models import TIL

        count = 0
        if self.content_type in ['blog', 'all']:
            count += Entry.objects.filter(tags=self).count()
            count += Blogmark.objects.filter(tags=self).count()
        if self.content_type in ['til', 'all']:
            count += TIL.objects.filter(tags=self).count()

        self.usage_count = count
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class Series(models.Model):
    """Collection of related posts forming a series"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    summary = models.TextField(blank=True, help_text="Brief summary for listing pages")
    cover_image = models.URLField(
        blank=True,
        null=True,
        help_text="Cover image URL for the series"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='series'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    # Display options
    is_complete = models.BooleanField(default=False, help_text="Is this series complete?")
    is_featured = models.BooleanField(default=False, help_text="Feature this series")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order for featured series")

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name = "Series"
        verbose_name_plural = "Series"
        ordering = ['-created']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:series', kwargs={'slug': self.slug})

    @property
    def entry_count(self):
        return self.series_entries.count()

    @property
    def published_entry_count(self):
        return self.series_entries.filter(entry__status='published').count()


class SeriesEntry(models.Model):
    """Through model for ordering entries in a series"""
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='series_entries')
    entry = models.ForeignKey('blog.Entry', on_delete=models.CASCADE, related_name='series_memberships')
    order = models.IntegerField(default=0, help_text="Order within the series")

    # Optional metadata
    part_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional title for this part (e.g., 'Part 1: Introduction')"
    )
    notes = models.TextField(blank=True, help_text="Internal notes about this entry's role in the series")

    added = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'core'
        ordering = ['order', 'added']
        unique_together = ['series', 'entry']
        verbose_name = "Series Entry"
        verbose_name_plural = "Series Entries"

    def __str__(self):
        if self.part_title:
            return f"{self.series.title} - {self.part_title}"
        return f"{self.series.title} - Part {self.order}"


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