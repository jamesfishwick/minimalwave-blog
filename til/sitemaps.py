"""
XML Sitemaps for TIL (Today I Learned) content.

Provides sitemap class for TIL posts to help search engines discover
short-form educational content.
"""

from django.contrib.sitemaps import Sitemap
from til.models import TIL


class TILSitemap(Sitemap):
    """Sitemap for TIL (Today I Learned) posts."""

    changefreq = "monthly"
    priority = 0.8  # High priority for valuable short-form content

    def items(self):
        """Return only non-draft TIL posts."""
        return TIL.objects.filter(is_draft=False).order_by('-created')

    def lastmod(self, obj):
        """Return the creation date (TIL posts typically don't update)."""
        return obj.created

    def location(self, obj):
        """Return the URL for the TIL post."""
        return obj.get_absolute_url()
