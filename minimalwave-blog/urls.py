from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import index as sitemap_index, sitemap
from django.views.generic import TemplateView
from blog.views_admin import run_auto_tag
from blog.sitemaps import EntrySitemap, BlogmarkSitemap
from til.sitemaps import TILSitemap
from core.views import test_anthropic_detection

# Sitemap configuration
sitemaps = {
    'entries': EntrySitemap,
    'blogmarks': BlogmarkSitemap,
    'til': TILSitemap,
}

urlpatterns = [
    path('admin/run-auto-tag/', run_auto_tag, name='run_auto_tag'),  # Webhook for running auto-tag
    path('admin/linkedin/', include('linkedin.linkedin_urls')),  # LinkedIn URLs must come before admin
    path('admin/', admin.site.urls),
    path('test-anthropic/', test_anthropic_detection, name='test_anthropic'),  # Debug view
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots_txt'),
    path('til/', include('til.urls')),
    path('', include('blog.urls')),  # Move blog URLs to end to avoid conflicts
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
