from django.db import models
from django.utils.html import strip_tags, mark_safe
from django.urls import reverse
from django.conf import settings
import markdown

from blog.models import BaseEntry
from blog.templatetags.markdown_extras import preprocess_image_shortcodes


class Project(BaseEntry):
    """
    A software project for the curated portfolio at /projects/.

    Inherits title/slug/status/publish_date/tags from BaseEntry (like Entry and
    Blogmark), but is a curated showcase rather than a chronological feed:
    - Flat slug URLs (/projects/<slug>/), not date-based ones.
    - Manual ordering via sort_order + featured, not -created.
    - Its own tech_stack facet, kept out of the shared blog tag namespace.
    """

    PROJECT_STATUS_CHOICES = (
        ('wip', 'Work in Progress'),
        ('active', 'Active'),
        ('shipped', 'Shipped'),
        ('archived', 'Archived'),
    )

    # Override the inherited slug: projects are not date-scoped, so drop
    # unique_for_date='created' in favour of a globally unique slug. Overriding a
    # field from an abstract base is supported by Django.
    slug = models.SlugField(unique=True)

    summary = models.TextField(
        help_text="Short description shown on the projects grid card (markdown)"
    )
    body = models.TextField(
        blank=True, help_text="Full write-up shown on the detail page (markdown)"
    )
    repo_url = models.URLField(blank=True, help_text="Source code repository URL")
    live_url = models.URLField(blank=True, help_text="Live site or demo URL")
    tech_stack = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated technologies, e.g. Django, PostgreSQL, HTMX",
    )
    project_status = models.CharField(
        max_length=10,
        choices=PROJECT_STATUS_CHOICES,
        default='active',
        help_text="Lifecycle state of the project itself (distinct from publish status)",
    )
    start_date = models.DateField(help_text="When work on the project began")
    end_date = models.DateField(
        null=True, blank=True, help_text="When the project shipped or was archived (blank = ongoing)"
    )
    featured = models.BooleanField(
        default=False, help_text="Highlight this project at the top of the grid"
    )
    sort_order = models.IntegerField(
        default=0, help_text="Lower numbers sort first in the curated grid"
    )
    screenshot = models.ImageField(
        upload_to='projects/images/%Y/%m/',
        blank=True,
        null=True,
        help_text="Screenshot or thumbnail for the card and social cards",
    )

    class Meta:
        ordering = ['sort_order', '-start_date']

    def save(self, *args, **kwargs):
        # Keep the legacy is_draft flag in sync with status, as Entry/Blogmark do.
        self.is_draft = self.status != 'published'
        super().save(*args, **kwargs)

    @property
    def tech_stack_list(self):
        """Split the comma-separated tech_stack into a list for chip rendering."""
        return [t.strip() for t in self.tech_stack.split(',') if t.strip()]

    @property
    def summary_rendered(self):
        processed = preprocess_image_shortcodes(self.summary)
        return mark_safe(markdown.markdown(
            processed,
            extensions=settings.MARKDOWN_EXTENSIONS,
            output_format=settings.MARKDOWN_OUTPUT_FORMAT,
        ))

    @property
    def summary_text(self):
        processed = preprocess_image_shortcodes(self.summary)
        return strip_tags(markdown.markdown(
            processed,
            extensions=settings.MARKDOWN_EXTENSIONS,
            output_format=settings.MARKDOWN_OUTPUT_FORMAT,
        ))

    @property
    def body_rendered(self):
        processed = preprocess_image_shortcodes(self.body)
        return mark_safe(markdown.markdown(
            processed,
            extensions=settings.MARKDOWN_EXTENSIONS,
            output_format=settings.MARKDOWN_OUTPUT_FORMAT,
        ))

    @property
    def get_image_url(self):
        """Effective image URL for the card and social/OpenGraph tags."""
        if self.screenshot:
            return self.screenshot.url
        return None

    def get_absolute_url(self):
        return reverse('projects:detail', kwargs={'slug': self.slug})
