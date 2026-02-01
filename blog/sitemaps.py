"""
XML Sitemaps for blog content.

Provides sitemap classes for all content types to help search engines
discover and index content efficiently.
"""

from django.contrib.sitemaps import Sitemap
from blog.models import Entry, Blogmark


class EntrySitemap(Sitemap):
    """Sitemap for blog entries (full posts)."""

    changefreq = "monthly"
    priority = 0.9  # High priority for main content

    def items(self):
        """Return only published entries."""
        return Entry.objects.filter(status='published').order_by('-created')

    def lastmod(self, obj):
        """Return the last modification date."""
        return obj.updated if hasattr(obj, 'updated') else obj.created

    def location(self, obj):
        """Return the URL for the entry."""
        return obj.get_absolute_url()


class BlogmarkSitemap(Sitemap):
    """Sitemap for blogmarks (link blog posts)."""

    changefreq = "monthly"
    priority = 0.7  # Slightly lower priority than full entries

    def items(self):
        """Return only published blogmarks."""
        return Blogmark.objects.filter(status='published').order_by('-created')

    def lastmod(self, obj):
        """Return the last modification date."""
        return obj.updated if hasattr(obj, 'updated') else obj.created

    def location(self, obj):
        """Return the URL for the blogmark."""
        return obj.get_absolute_url()
