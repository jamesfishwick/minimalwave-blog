"""
XML Sitemap for the projects portfolio.

Exposes published projects so search engines can discover the showcase.
"""

from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from django.db import models

from projects.models import Project


class ProjectSitemap(Sitemap):
    """Sitemap for portfolio projects."""

    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Project.objects.filter(
            status='published'
        ).filter(
            models.Q(publish_date__isnull=True) | models.Q(publish_date__lte=timezone.now())
        )

    def lastmod(self, obj):
        return obj.end_date or obj.start_date

    def location(self, obj):
        return obj.get_absolute_url()
