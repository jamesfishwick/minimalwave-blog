# Image Functionality Tests

Comprehensive test coverage for image upload, processing, and storage functionality.

## Test Files

### `test_images.py`
**Core image functionality tests**

- **ImageFieldTests**: Verify image fields exist on Entry, Blogmark, and TIL models
- **ImageUploadTests**: Test image upload to local storage, path organization
- **ImageURLTests**: Test `get_image_url` property and fallback behavior
- **ImageAltTextTests**: Verify accessibility alt text storage
- **ImageMigrationTests**: Backward compatibility with existing entries

**Coverage**: Model fields, basic upload, URL generation, legacy compatibility

### `test_image_processing.py`
**Image optimization and processing tests**

- **ImageOptimizationTests**:
  - Resize large images to max_width
  - Preserve small images (no upscaling)
  - Quality parameter effects
  - Format conversion (PNG → JPEG, WebP)
  - RGBA → RGB conversion
  - Aspect ratio preservation

- **ThumbnailGenerationTests**:
  - Default and custom thumbnail sizes
  - Aspect ratio maintenance
  - RGBA → RGB conversion
  - File size reduction

- **ImageProcessingEdgeCasesTests**:
  - Very small images
  - Square images
  - Portrait orientation

**Coverage**: Image optimization utilities, thumbnail generation, edge cases

### `test_image_storage.py`
**Storage backend integration tests**

- **LocalStorageTests**: Development environment local file storage
- **AzureBlobStorageConfigTests**: Production Azure configuration
- **StorageBackendTests**: Backend configuration and switching
- **ImageURLIntegrationTests**: URL generation across storage backends
- **ImageStoragePathTests**: Upload path structure validation

**Coverage**: Local storage, Azure Blob Storage config, URL generation, path organization

## Running Tests

### Run All Image Tests
```bash
# Local development
python manage.py test tests.test_images tests.test_image_processing tests.test_image_storage

# In Docker
docker-compose exec web python manage.py test tests.test_images tests.test_image_processing tests.test_image_storage
```

### Run Specific Test Classes
```bash
# Image field tests only
python manage.py test tests.test_images.ImageFieldTests

# Optimization tests only
python manage.py test tests.test_image_processing.ImageOptimizationTests

# Storage tests only
python manage.py test tests.test_image_storage.LocalStorageTests
```

### Run Individual Tests
```bash
# Test image upload
python manage.py test tests.test_images.ImageUploadTests.test_entry_image_upload

# Test image resize
python manage.py test tests.test_image_processing.ImageOptimizationTests.test_optimize_image_resizes_large_images

# Test URL generation
python manage.py test tests.test_images.ImageURLTests.test_entry_get_image_url_with_upload
```

## CI/CD Integration

Tests are automatically run in GitHub Actions deployment workflow:

```yaml
- name: Run image functionality tests
  run: |
    export DJANGO_SETTINGS_MODULE=minimalwave-blog.settings.ci
    poetry run python manage.py test tests.test_images tests.test_image_processing tests.test_image_storage
```

Deployment is blocked if any image tests fail.

## Test Coverage

### Models (Entry, Blogmark, TIL)
- ✅ Image field presence
- ✅ Image alt text field
- ✅ Legacy card_image compatibility
- ✅ get_image_url property logic
- ✅ Upload path organization

### Image Processing
- ✅ Resize to max_width (default 1200px)
- ✅ Quality optimization (default 85%)
- ✅ Format conversion (PNG → JPEG, WebP)
- ✅ RGBA → RGB conversion
- ✅ Aspect ratio preservation
- ✅ Thumbnail generation

### Storage Backends
- ✅ Local file storage (development)
- ✅ Azure Blob Storage configuration (production)
- ✅ MEDIA_URL generation
- ✅ Upload path structure (blog/images/YYYY/MM/)

### Integration
- ✅ URL generation across storage backends
- ✅ Priority: uploaded image > card_image URL
- ✅ Backward compatibility with existing entries
- ✅ Admin interface image upload

## Manual Testing

### Local Development
1. Start Docker: `make dev-safe`
2. Access admin: http://localhost:8000/admin/
3. Create Entry with image upload
4. Verify image displays on entry detail page
5. Check `/media/blog/images/` directory

### Production (After Deployment)
1. Access admin: https://jamesfishwick.com/admin/
2. Create Entry with image upload
3. Verify image uploads to Azure Blob Storage
4. Check Azure Portal → Storage Account → media container
5. Verify image URL is `https://minimalwavestorage.blob.core.windows.net/media/...`
6. Verify image displays on blog post

## Test Data

### Sample Images Used
- **Large image**: 2000x1500px (tests resize)
- **Small image**: 800x600px (tests no upscale)
- **Portrait image**: 600x1200px (tests orientation)
- **Square image**: 1000x1000px (tests aspect ratio)
- **RGBA image**: PNG with transparency (tests conversion)

### Expected Behavior
- Images > 1200px width → resized to 1200px
- Images < 1200px → kept original size
- RGBA images → converted to RGB for JPEG
- Quality: 85% (good balance of size/quality)
- Thumbnails: fit within 300x300px

## Adding New Tests

### Template for New Test Class
```python
from django.test import TestCase
from blog.models import Entry

class MyNewImageTests(TestCase):
    """Test description."""

    def setUp(self):
        # Setup code
        pass

    def test_specific_feature(self):
        """Test that specific feature works."""
        # Arrange
        entry = Entry.objects.create(...)

        # Act
        result = entry.some_method()

        # Assert
        self.assertEqual(result, expected)
```

### Best Practices
1. Use descriptive test names: `test_what_is_being_tested`
2. Include docstrings explaining the test purpose
3. Use helper methods to create test images
4. Clean up temporary files with `@override_settings(MEDIA_ROOT=tempfile.mkdtemp())`
5. Test both success and edge cases
6. Verify file existence for upload tests
7. Check URL format for storage tests

## Troubleshooting

### Tests Failing Locally
```bash
# Check Pillow is installed
pip list | grep -i pillow

# Check MEDIA_ROOT is writable
python manage.py shell
>>> from django.conf import settings
>>> import os
>>> os.access(settings.MEDIA_ROOT, os.W_OK)
```

### Tests Failing in CI/CD
- Check `minimalwave-blog.settings.ci` exists and configures in-memory database
- Verify Pillow is in `pyproject.toml` dependencies
- Check test database has proper permissions

### Image Upload Tests Fail
- Ensure `MEDIA_ROOT` is set in test settings
- Use `@override_settings(MEDIA_ROOT=tempfile.mkdtemp())` decorator
- Check file permissions on media directory

## Future Test Additions

Potential areas for expansion:
- [ ] Admin interface integration tests (Selenium/Playwright)
- [ ] Image deletion tests (orphaned files)
- [ ] Multiple image upload tests
- [ ] Image format validation (reject invalid formats)
- [ ] File size limit tests
- [ ] Concurrent upload tests
- [ ] Azure Blob Storage error handling
- [ ] Image CDN integration tests
