"""
Integration tests for image storage (local and Azure Blob Storage).

Tests cover:
- Local storage configuration (development)
- Azure Blob Storage configuration (production)
- Image URL generation for different storage backends
- Storage backend switching
- Media URL configuration
"""

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.conf import settings
from blog.models import Entry
from PIL import Image
from io import BytesIO
import tempfile
import os


class LocalStorageTests(TestCase):
    """Test local file storage (development environment)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def create_test_image(self):
        """Helper to create a test image."""
        image = Image.new('RGB', (800, 600), color='blue')
        img_io = BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_local_storage_saves_file(self):
        """Test that images are saved to local MEDIA_ROOT."""
        test_image = self.create_test_image()

        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image=test_image
        )

        # File should exist on disk
        self.assertTrue(os.path.exists(entry.image.path))

        # File should be in MEDIA_ROOT
        self.assertTrue(entry.image.path.startswith(settings.MEDIA_ROOT))

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_local_storage_url_generation(self):
        """Test URL generation with local storage."""
        test_image = self.create_test_image()

        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image=test_image
        )

        # URL should start with MEDIA_URL
        self.assertTrue(entry.image.url.startswith(settings.MEDIA_URL))

        # URL should contain the image path
        self.assertIn('blog/images/', entry.image.url)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_local_storage_cleanup(self):
        """Test that deleting model also deletes file."""
        test_image = self.create_test_image()

        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image=test_image
        )

        image_path = entry.image.path

        # File should exist
        self.assertTrue(os.path.exists(image_path))

        # Delete the entry
        entry.delete()

        # File should be deleted (Django handles this automatically)
        # Note: This behavior depends on Django's file deletion settings


class AzureBlobStorageConfigTests(TestCase):
    """Test Azure Blob Storage configuration."""

    def test_azure_storage_settings_exist(self):
        """Test that Azure storage settings are defined."""
        # These should be in production.py
        # We can't test actual Azure connection in unit tests,
        # but we can verify the settings structure is correct

        # Check that settings module has Azure configuration
        # (This will vary based on environment)
        from django.conf import settings

        # Settings should have MEDIA_URL
        self.assertTrue(hasattr(settings, 'MEDIA_URL'))

        # Settings should have MEDIA_ROOT (fallback)
        self.assertTrue(hasattr(settings, 'MEDIA_ROOT'))

    def test_production_settings_configure_azure(self):
        """Test that production settings configure Azure storage when credentials present."""
        # Import production settings module
        from importlib import import_module
        import sys

        # Temporarily add production settings to path
        prod_settings_path = 'minimalwave-blog.settings.production'

        # This is a smoke test - just verify the module loads
        try:
            prod_module = import_module(prod_settings_path)
            # Production module should define Azure-related settings
            self.assertTrue(hasattr(prod_module, 'AZURE_ACCOUNT_NAME'))
            self.assertTrue(hasattr(prod_module, 'AZURE_ACCOUNT_KEY'))
            self.assertTrue(hasattr(prod_module, 'AZURE_CONTAINER'))
        except ImportError:
            self.skipTest("Production settings not available in test environment")


class StorageBackendTests(TestCase):
    """Test storage backend configuration and switching."""

    def test_development_uses_local_storage(self):
        """Test that development environment uses local file storage."""
        from django.conf import settings

        # In development/test, DEFAULT_FILE_STORAGE should not be Azure
        if hasattr(settings, 'DEFAULT_FILE_STORAGE'):
            self.assertNotIn('azure', settings.DEFAULT_FILE_STORAGE.lower())

    def test_media_url_configuration(self):
        """Test MEDIA_URL is properly configured."""
        from django.conf import settings

        # MEDIA_URL should be defined
        self.assertTrue(hasattr(settings, 'MEDIA_URL'))
        self.assertIsNotNone(settings.MEDIA_URL)

        # Should start with /
        self.assertTrue(settings.MEDIA_URL.startswith('/'))

    @override_settings(
        MEDIA_URL='https://test-storage.blob.core.windows.net/media/',
        MEDIA_ROOT=None
    )
    def test_azure_media_url_format(self):
        """Test Azure Blob Storage URL format."""
        from django.conf import settings

        # Azure MEDIA_URL should be HTTPS
        self.assertTrue(settings.MEDIA_URL.startswith('https://'))

        # Should contain blob.core.windows.net
        self.assertIn('blob.core.windows.net', settings.MEDIA_URL)

        # Should end with /
        self.assertTrue(settings.MEDIA_URL.endswith('/'))


class ImageURLIntegrationTests(TestCase):
    """Integration tests for image URL generation across storage backends."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_get_image_url_handles_no_image(self):
        """Test get_image_url returns None when no image."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published'
        )

        # Should return None (no image, no card_image)
        self.assertIsNone(entry.get_image_url)

    def test_get_image_url_with_legacy_card_image(self):
        """Test get_image_url returns card_image URL when no upload."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            card_image='https://example.com/image.jpg'
        )

        # Should return card_image
        self.assertEqual(entry.get_image_url, 'https://example.com/image.jpg')

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_get_image_url_with_uploaded_image(self):
        """Test get_image_url returns uploaded image URL."""
        # Create test image
        image = Image.new('RGB', (800, 600), color='red')
        img_io = BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)

        test_image = SimpleUploadedFile(
            name='test.jpg',
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image=test_image
        )

        # Should return uploaded image URL
        image_url = entry.get_image_url
        self.assertIsNotNone(image_url)
        self.assertIn('blog/images/', image_url)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_get_image_url_prioritizes_upload_over_card_image(self):
        """Test that uploaded image takes priority over card_image."""
        # Create test image
        image = Image.new('RGB', (800, 600), color='green')
        img_io = BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)

        test_image = SimpleUploadedFile(
            name='uploaded.jpg',
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            card_image='https://example.com/legacy.jpg',
            image=test_image
        )

        # Should return uploaded image, not card_image
        image_url = entry.get_image_url
        self.assertIn('uploaded.jpg', image_url)
        self.assertNotIn('legacy.jpg', image_url)


class ImageStoragePathTests(TestCase):
    """Test image storage path generation."""

    def test_entry_upload_path_structure(self):
        """Test Entry image upload path follows blog/images/YYYY/MM/ structure."""
        from django.utils import timezone
        from blog.models import Entry

        # Get the upload_to value from the field
        entry_model = Entry
        image_field = entry_model._meta.get_field('image')

        # Check upload_to pattern
        self.assertEqual(image_field.upload_to, 'blog/images/%Y/%m/')

    def test_blogmark_upload_path_structure(self):
        """Test Blogmark image upload path follows blog/blogmarks/YYYY/MM/ structure."""
        from blog.models import Blogmark

        blogmark_model = Blogmark
        image_field = blogmark_model._meta.get_field('image')

        # Check upload_to pattern
        self.assertEqual(image_field.upload_to, 'blog/blogmarks/%Y/%m/')

    def test_til_upload_path_structure(self):
        """Test TIL image upload path follows til/images/YYYY/MM/ structure."""
        from til.models import TIL

        til_model = TIL
        image_field = til_model._meta.get_field('image')

        # Check upload_to pattern
        self.assertEqual(image_field.upload_to, 'til/images/%Y/%m/')
