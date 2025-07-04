# LinkedIn Integration Database Schema Design

## 1. LinkedInCredentials Model
Stores OAuth tokens and app credentials for LinkedIn API access.

```python
class LinkedInCredentials(models.Model):
    """
    Stores LinkedIn OAuth credentials and app configuration.
    Should be a singleton model - only one instance should exist.
    """
    # App credentials
    client_id = models.CharField(max_length=255, help_text="LinkedIn App Client ID")
    client_secret = models.CharField(max_length=255, help_text="LinkedIn App Client Secret")
    
    # OAuth tokens
    access_token = models.TextField(help_text="LinkedIn OAuth access token")
    refresh_token = models.TextField(blank=True, null=True, help_text="LinkedIn OAuth refresh token")
    token_expires_at = models.DateTimeField(help_text="When the access token expires")
    
    # OAuth flow state
    state = models.CharField(max_length=128, blank=True, null=True, help_text="OAuth state for CSRF protection")
    
    # Metadata
    authorized_user = models.CharField(max_length=255, help_text="LinkedIn user who authorized the app")
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
```

## 2. LinkedInPost Model
Tracks LinkedIn posts that have been published from blog entries.

```python
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
    post_text = models.TextField(help_text="Text content posted to LinkedIn")
    
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
```

## 3. Add LinkedIn fields to Entry model
Extend the existing Entry model with LinkedIn-specific fields.

```python
# Add these fields to the Entry model:

# LinkedIn integration fields
linkedin_enabled = models.BooleanField(
    default=True,
    help_text="Automatically post to LinkedIn when published"
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

@property
def linkedin_post_text(self):
    """Get the text that should be posted to LinkedIn"""
    if self.linkedin_custom_text:
        return self.linkedin_custom_text
    return self.summary_text  # Use the existing summary_text property
```

## 4. LinkedInSettings Model (Optional)
For additional configuration options.

```python
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
```

## Migration Strategy

1. Create initial migration for LinkedInCredentials and LinkedInPost models
2. Create separate migration to add LinkedIn fields to Entry model
3. Create data migration to set default values if needed
4. Create LinkedInSettings model in final migration

## Security Considerations

- Store client_secret and tokens using Django's encryption
- Consider using django-encrypted-fields for sensitive data
- Implement token refresh logic
- Add proper field validation
- Use environment variables for client credentials in production

## Integration Points

- LinkedInCredentials: Used by OAuth flow and API service
- LinkedInPost: Created when posts are successfully published
- Entry.linkedin_*: Controls posting behavior per entry
- LinkedInSettings: Global configuration