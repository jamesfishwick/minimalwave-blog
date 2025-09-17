from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/linkedin/', include('linkedin.linkedin_urls')),  # LinkedIn URLs must come before admin
    path('admin/', admin.site.urls),
    path('til/', include('til.urls')),
    path('', include('blog.urls')),  # Move blog URLs to end to avoid conflicts
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
