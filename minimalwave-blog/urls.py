from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

from blog.sitemaps import BlogmarkSitemap, EntrySitemap
from blog.views_admin import run_auto_tag
from core.views import test_anthropic_detection
from projects.sitemaps import ProjectSitemap

# Sitemap configuration
sitemaps = {
    "entries": EntrySitemap,
    "blogmarks": BlogmarkSitemap,
    "projects": ProjectSitemap,
}

urlpatterns = [
    path(
        "admin/run-auto-tag/", run_auto_tag, name="run_auto_tag"
    ),  # Webhook for running auto-tag
    path("admin/", admin.site.urls),
    path(
        "test-anthropic/", test_anthropic_detection, name="test_anthropic"
    ),  # Debug view
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),
    path(
        "favicon.ico",
        RedirectView.as_view(
            url="/" + settings.STATIC_URL.strip("/") + "/images/favicon.ico",
            permanent=True,
        ),
        name="favicon",
    ),
    path("til/", include("til.urls")),  # Retired section: 301-redirects into blog
    path("projects/", include("projects.urls")),
    path("", include("blog.urls")),  # Move blog URLs to end to avoid conflicts
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
