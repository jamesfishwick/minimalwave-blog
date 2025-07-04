from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/linkedin/', include('blog.linkedin_urls')),
    path('til/', include('til.urls')),
    path('', include('blog.urls')),  # Move blog URLs to end to avoid conflicts
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
