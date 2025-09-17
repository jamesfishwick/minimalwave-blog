from django.db import models
from django.utils import timezone


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
        app_label = 'linkedin'
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
    # Link to the blog entry - using string reference to avoid circular import
    entry = models.ForeignKey('blog.Entry', on_delete=models.CASCADE, related_name='linkedin_posts')

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
        app_label = 'linkedin'
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
        app_label = 'linkedin'
        verbose_name = "LinkedIn Settings"
        verbose_name_plural = "LinkedIn Settings"

    def __str__(self):
        return "LinkedIn Settings"

    @classmethod
    def get_settings(cls):
        """Get or create the settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


# Note: Entry is imported as a string reference above to avoid circular imports
# Views should import Entry directly from blog.models instead