"""
XML Sitemap for the projects portfolio.

Exposes published projects so search engines can discover the showcase.
"""

from django.contrib.sitemaps import Sitemap

from projects.models import Project


class ProjectSitemap(Sitemap):
    """Sitemap for portfolio projects."""

    changefreq = "monthly"
    priority = 0.7

    def items(self):
        # Single source of truth for "published" — shared with the views/feed.
        return Project.objects.published()

    def lastmod(self, obj):
        return obj.end_date or obj.start_date

    def location(self, obj):
        return obj.get_absolute_url()
