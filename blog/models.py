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


class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:tag', kwargs={'slug': self.slug})

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
    tags = models.ManyToManyField(Tag, blank=True)
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


class LinkedInCredentials(models.Model):
    """
    Stores LinkedIn OAuth credentials and app configuration.
    Should be a singleton model - only one instance should exist.
    """
    # App credentials
    client_id = models.CharField(max_length=255, help_text="LinkedIn App Client ID")
    client_secret = models.CharField(max_length=255, help_text="LinkedIn App Client Secret")
    
    # OAuth tokens
    access_token = models.TextField(blank=True, default='', help_text="LinkedIn OAuth access token")
    refresh_token = models.TextField(blank=True, null=True, help_text="LinkedIn OAuth refresh token")
    token_expires_at = models.DateTimeField(null=True, blank=True, help_text="When the access token expires")
    
    # OAuth flow state
    state = models.CharField(max_length=128, blank=True, null=True, help_text="OAuth state for CSRF protection")
    
    # Metadata
    authorized_user = models.CharField(max_length=255, help_text="LinkedIn user who authorized the app", default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "LinkedIn Credentials"
        verbose_name_plural = "LinkedIn Credentials"
    
    def __str__(self):
        return f"LinkedIn Credentials (expires: {self.token_expires_at})"
    
    @classmethod
    def get_credentials(cls):
        """Get the singleton credentials instance"""
        return cls.objects.first()
    
    @property
    def is_token_valid(self):
        """Check if access token is still valid"""
        return self.token_expires_at > timezone.now()


class LinkedInPost(models.Model):
    """
    Tracks LinkedIn posts created from blog entries.
    """
    # Link to the blog entry
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='linkedin_posts')
    
    # LinkedIn post details
    linkedin_post_id = models.CharField(max_length=255, unique=True, help_text="LinkedIn post URN")
    post_url = models.URLField(blank=True, null=True, help_text="URL to the LinkedIn post")
    
    # Post content
    post_text = models.TextField(blank=True, default='', help_text="Text content posted to LinkedIn")
    
    # Metadata
    posted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('posted', 'Posted'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error message if posting failed")
    
    class Meta:
        verbose_name = "LinkedIn Post"
        verbose_name_plural = "LinkedIn Posts"
        ordering = ['-posted_at']
    
    def __str__(self):
        return f"LinkedIn post for: {self.entry.title}"


class LinkedInSettings(models.Model):
    """
    LinkedIn integration settings.
    Singleton model for configuration.
    """
    enabled = models.BooleanField(
        default=True,
        help_text="Enable LinkedIn integration globally"
    )
    auto_post_entries = models.BooleanField(
        default=True,
        help_text="Automatically post blog entries to LinkedIn"
    )
    auto_post_blogmarks = models.BooleanField(
        default=False,
        help_text="Automatically post blogmarks to LinkedIn"
    )
    include_url = models.BooleanField(
        default=True,
        help_text="Include blog post URL in LinkedIn posts"
    )
    url_template = models.CharField(
        max_length=255,
        default="Read more: {url}",
        help_text="Template for including URL in posts"
    )
    
    class Meta:
        verbose_name = "LinkedIn Settings"
        verbose_name_plural = "LinkedIn Settings"
    
    def __str__(self):
        return "LinkedIn Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create the settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
