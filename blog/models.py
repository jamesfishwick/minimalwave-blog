from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import strip_tags
import markdown
from django.utils.html import mark_safe
from django.urls import reverse


class SiteSettings(models.Model):
    """
    Singleton model for storing site-wide settings.
    Only one instance of this model should exist.
    """
    site_title = models.CharField(
        max_length=100,
        default="Minimal Wave Blog",
        help_text="The title of your blog"
    )
    site_description = models.TextField(
        default="A personal blog with minimal wave aesthetics",
        help_text="The description of your blog"
    )
    header_logo = models.ImageField(
        upload_to='site_settings/',
        null=True,
        blank=True,
        help_text="Logo to display in the header (optional)"
    )
    favicon = models.ImageField(
        upload_to='site_settings/',
        null=True,
        blank=True,
        help_text="Site favicon (optional)"
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    @classmethod
    def get_settings(cls):
        """Get or create the site settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


# Tag model moved to core.models.EnhancedTag

class BaseEntry(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('published', 'Published'),
    )
    title = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)
    publish_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Schedule this content to be published at a future date and time"
    )
    slug = models.SlugField(unique_for_date='created')
    tags = models.ManyToManyField('core.EnhancedTag', blank=True)
    is_draft = models.BooleanField(
        default=False,
        help_text="Legacy field. Use 'status' instead.",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Draft entries are only visible to logged-in users with the preview link"
    )

    @property
    def is_published(self):
        """Check if the entry is published and not scheduled for future"""
        if self.status != 'published':
            return False
        if self.publish_date and self.publish_date > timezone.now():
            return False
        return not self.is_draft  # Additional check for backward compatibility

    class Meta:
        abstract = True
        ordering = ['-created']

    def __str__(self):
        return self.title

    # Legacy method for backward compatibility
    def check_published(self):
        """Legacy method - use is_published property instead"""
        return self.is_published

class Entry(BaseEntry):
    summary = models.TextField()
    body = models.TextField()
    card_image = models.URLField(
        blank=True, null=True, help_text="URL to image for social media cards"
    )
    authors = models.ManyToManyField(User, through="Authorship", blank=True)
    
    # LinkedIn integration fields
    linkedin_enabled = models.BooleanField(
        default=False,
        help_text="Automatically post to LinkedIn when published (currently disabled)"
    )
    linkedin_custom_text = models.TextField(
        blank=True,
        null=True,
        help_text="Custom text for LinkedIn post (leave blank to use summary)"
    )
    linkedin_posted = models.BooleanField(
        default=False,
        help_text="Whether this entry has been posted to LinkedIn"
    )

    class Meta:
        verbose_name_plural = "entries"
        ordering = ['-created']

    def save(self, *args, **kwargs):
        # Ensure consistency between status and is_draft fields
        if self.status == 'published':
            self.is_draft = False
        else:
            self.is_draft = True
        super().save(*args, **kwargs)

    @property
    def summary_rendered(self):
        return mark_safe(markdown.markdown(
            self.summary, 
            extensions=['extra', 'codehilite'],
            output_format="html5"
        ))

    @property
    def summary_text(self):
        return strip_tags(markdown.markdown(
            self.summary, 
            extensions=['extra', 'codehilite'],
            output_format="html5"
        ))

    @property
    def body_rendered(self):
        return mark_safe(markdown.markdown(
            self.body, 
            extensions=['extra', 'codehilite'],
            output_format="html5"
        ))

    def get_absolute_url(self):
        return reverse('blog:entry', kwargs={
            'year': self.created.year,
            'month': self.created.strftime('%b').lower(),
            'day': self.created.day,
            'slug': self.slug
        })

    def get_preview_url(self):
        """Get URL for previewing draft entries"""
        return reverse('blog:entry_preview', kwargs={
            'slug': self.slug
        })
    
    @property
    def linkedin_post_text(self):
        """Get the text that should be posted to LinkedIn"""
        if self.linkedin_custom_text:
            return self.linkedin_custom_text
        return self.summary_text  # Use the existing summary_text property

class Authorship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "authorships"

class Blogmark(BaseEntry):
    """Link blog implementation similar to Simon's 'blogmarks'"""
    url = models.URLField()
    commentary = models.TextField()
    via = models.URLField(blank=True, null=True, help_text="URL of where you found the link")
    via_title = models.CharField(max_length=200, blank=True, null=True, help_text="Title of where you found the link")

    def save(self, *args, **kwargs):
        # Ensure consistency between status and is_draft fields
        if self.status == 'published':
            self.is_draft = False
        else:
            self.is_draft = True
        super().save(*args, **kwargs)

    @property
    def commentary_rendered(self):
        return mark_safe(markdown.markdown(
            self.commentary, 
            extensions=['extra', 'codehilite'],
            output_format="html5"
        ))

    def get_absolute_url(self):
        return reverse('blog:blogmark', kwargs={
            'year': self.created.year,
            'month': self.created.strftime('%b').lower(),
            'day': self.created.day,
            'slug': self.slug
        })

    def get_preview_url(self):
        """Get URL for previewing draft blogmarks"""
        return reverse('blog:blogmark_preview', kwargs={
            'slug': self.slug
        })

# LinkedIn models moved to linkedin app
