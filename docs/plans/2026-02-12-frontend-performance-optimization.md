# Frontend Performance Optimization

**Date:** 2026-02-12
**Status:** Approved
**Priority:** Optional Enhancement

## Context

Site is already performant with small assets (107KB image, 36KB CSS total). These optimizations are "nice to have" for progressive enhancement, not critical fixes.

## Current Baseline

- CSS: 28KB (style.css) + 8.5KB (additional.css) = 36.5KB total
- Images: 107KB (default-card.jpg) + user-uploaded content
- JavaScript: Minimal (no bundler currently)
- Already optimized: Design tokens, removed excess gradients/shadows

## Optimization Opportunities

### 1. Asset Minification & Compression

**Current state:** Development CSS (unminified)
**Target:** Minified CSS, compressed with Brotli/gzip

**Implementation:**
```python
# minimalwave-blog/settings/production.py
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# This enables:
# - Automatic CSS/JS minification
# - Brotli compression (falls back to gzip)
# - Content-addressable URLs (cache busting)
```

**Expected improvement:**
- CSS: 36KB → ~25KB minified → ~8KB compressed
- Faster initial page load (28KB less to download)

---

### 2. Image Optimization

**Current state:** JPEG images, no lazy loading
**Target:** WebP format, lazy loading, responsive images

**a) WebP Conversion**
```python
# blog/models.py - Add ImageField with WebP support
from django.core.files.base import ContentFile
from PIL import Image
import io

def save_webp_variant(image_field):
    """Convert uploaded image to WebP"""
    img = Image.open(image_field)
    webp_io = io.BytesIO()
    img.save(webp_io, format='WEBP', quality=85)
    webp_io.seek(0)

    webp_name = image_field.name.replace('.jpg', '.webp').replace('.png', '.webp')
    return ContentFile(webp_io.read(), name=webp_name)

# Usage in Entry/Blogmark models:
class Entry(BaseEntry):
    image = models.ImageField(upload_to='images/', blank=True)
    image_webp = models.ImageField(upload_to='images/', blank=True, editable=False)

    def save(self, *args, **kwargs):
        if self.image and not self.image_webp:
            self.image_webp = save_webp_variant(self.image)
        super().save(*args, **kwargs)
```

**b) Lazy Loading**
```html
<!-- templates/blog/entry.html -->
{% if entry.image %}
  <picture>
    <source srcset="{{ entry.image_webp.url }}" type="image/webp">
    <img src="{{ entry.image.url }}"
         alt="{{ entry.title }}"
         loading="lazy"
         width="800"
         height="450">
  </picture>
{% endif %}
```

**c) Responsive Images**
```python
# Use django-imagekit or easy-thumbnails
from easy_thumbnails.fields import ThumbnailerImageField

class Entry(BaseEntry):
    image = ThumbnailerImageField(upload_to='images/', blank=True)

# Template:
{% load thumbnail %}
<img src="{% thumbnail entry.image 800x450 %}"
     srcset="{% thumbnail entry.image 400x225 %} 400w,
             {% thumbnail entry.image 800x450 %} 800w"
     sizes="(max-width: 768px) 400px, 800px"
     loading="lazy">
```

**Expected improvement:**
- WebP: 30-50% smaller than JPEG
- Lazy loading: Faster initial page load (deferred image loading)
- Responsive images: Mobile users download smaller images

---

### 3. Service Worker for Offline Support

**Target:** Progressive Web App (PWA) with offline reading

**Implementation:**
```javascript
// static/js/service-worker.js
const CACHE_NAME = 'minimalwave-v1';
const OFFLINE_URL = '/offline/';

const STATIC_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/css/additional.css',
  OFFLINE_URL
];

// Install: Cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

// Fetch: Network-first, fall back to cache
self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(OFFLINE_URL);
      })
    );
  } else {
    event.respondWith(
      caches.match(event.request).then(response => {
        return response || fetch(event.request);
      })
    );
  }
});
```

**Registration:**
```html
<!-- templates/base.html -->
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/js/service-worker.js');
}
</script>
```

**Offline page:**
```html
<!-- templates/offline.html -->
{% extends "base.html" %}
{% block content %}
<div class="offline-message">
  <h1>You're offline</h1>
  <p>This page isn't available offline. Check your connection.</p>
  <p>Cached posts:</p>
  <ul id="cached-posts"></ul>
</div>
{% endblock %}
```

**Expected improvement:**
- Offline reading for visited pages
- Faster repeat visits (cached assets)
- PWA installable on mobile devices

---

### 4. HTTP/2 Server Push (via Azure)

**Current:** Sequential asset loading
**Target:** Push critical CSS with HTML response

**Azure Static Web Apps configuration:**
```json
// staticwebapp.config.json
{
  "routes": [
    {
      "route": "/*",
      "headers": {
        "Link": "</static/css/style.css>; rel=preload; as=style"
      }
    }
  ]
}
```

**Alternative (Django templates):**
```html
<!-- templates/base.html -->
<link rel="preload" href="{% static 'css/style.css' %}" as="style">
<link rel="preload" href="{% static 'css/additional.css' %}" as="style">
```

**Expected improvement:**
- Critical CSS loads in parallel with HTML
- Faster first contentful paint (FCP)

---

## Implementation Checklist

### Phase 1: Low-Hanging Fruit
- [ ] Enable `CompressedManifestStaticFilesStorage` in production
- [ ] Add `loading="lazy"` to all `<img>` tags
- [ ] Add `<link rel="preload">` for critical CSS
- [ ] Test Lighthouse score improvement

### Phase 2: Image Optimization
- [ ] Install `Pillow` and `easy-thumbnails`
- [ ] Add WebP conversion to image upload
- [ ] Update templates with `<picture>` element
- [ ] Generate responsive image sizes
- [ ] Test on mobile devices

### Phase 3: Service Worker (PWA)
- [ ] Create `service-worker.js`
- [ ] Create offline fallback page
- [ ] Register service worker in base template
- [ ] Add PWA manifest.json
- [ ] Test offline functionality
- [ ] Add "Add to Home Screen" prompt

### Phase 4: Advanced Optimizations
- [ ] HTTP/2 server push configuration
- [ ] Font subsetting (if using custom fonts)
- [ ] Critical CSS inlining
- [ ] Preconnect to external domains

## Performance Targets

**Current (estimated):**
- Lighthouse Performance: 85-90
- First Contentful Paint: 1.2s
- Largest Contentful Paint: 1.8s
- Total Blocking Time: 150ms

**Target (post-optimization):**
- Lighthouse Performance: 95+
- First Contentful Paint: 0.8s
- Largest Contentful Paint: 1.2s
- Total Blocking Time: 50ms

## Browser Compatibility

- **WebP:** Chrome 23+, Firefox 65+, Safari 14+ (2020+)
- **Service Workers:** Chrome 40+, Firefox 44+, Safari 11.1+
- **HTTP/2 Push:** All modern browsers
- **Lazy loading:** Chrome 77+, Firefox 75+, Safari 15.4+

Fallbacks included for older browsers.

## Dependencies

```txt
# requirements.txt additions
Pillow>=10.0.0  # Image processing
easy-thumbnails>=2.8.5  # Responsive images
django-storages>=1.14  # Optional: S3/Azure Blob storage
```

## Notes

- Start with Phase 1 (easy wins, no code changes)
- Phase 2 & 3 are more involved but high impact
- Service worker requires HTTPS (already have via Azure)
- Monitor Core Web Vitals in production
