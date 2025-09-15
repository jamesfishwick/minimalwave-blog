from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import strip_tags, mark_safe
import markdown
from django.urls import reverse
from blog.models import Tag

class TIL(models.Model):
    """Today I Learned model for short-form content organized by topic"""
    title = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)
    slug = models.SlugField(unique_for_date='created')
    body = models.TextField()
    card_image = models.URLField(
        blank=True, null=True, help_text="URL to image for social media cards"
    )
    tags = models.ManyToManyField(Tag, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    is_draft = models.BooleanField(
        default=False,
        help_text="Draft TILs do not show in index pages but can be visited directly if you know the URL",
    )
    
    # LinkedIn integration fields
    linkedin_enabled = models.BooleanField(
        default=False,
        help_text="Automatically post to LinkedIn when published"
    )
    linkedin_custom_text = models.TextField(
        blank=True,
        null=True,
        help_text="Custom text for LinkedIn post (leave blank to use body)"
    )
    linkedin_posted = models.BooleanField(
        default=False,
        help_text="Whether this TIL has been posted to LinkedIn"
    )

    class Meta:
        ordering = ['-created']
        verbose_name = "TIL"
        verbose_name_plural = "TILs"

    def __str__(self):
        return self.title

    @property
    def body_rendered(self):
        return mark_safe(markdown.markdown(
            self.body, 
            extensions=['extra', 'codehilite'],
            output_format="html5"
        ))

    @property
    def body_text(self):
        return strip_tags(markdown.markdown(
            self.body, 
            extensions=['extra', 'codehilite'],
            output_format="html5"
        ))

    def get_absolute_url(self):
        return reverse('til:detail', kwargs={
            'year': self.created.year,
            'month': self.created.strftime('%b').lower(),
            'day': self.created.day,
            'slug': self.slug
        })
    
    @property
    def linkedin_post_text(self):
        """Get the text that should be posted to LinkedIn"""
        if self.linkedin_custom_text:
            return self.linkedin_custom_text
        return self.body_text  # Use the existing body_text property
