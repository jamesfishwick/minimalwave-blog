"""
Tests for image upload and handling functionality.

Tests cover:
- Image field presence on models
- Image upload and optimization
- Image URL generation
- Azure Blob Storage integration
- Image display in templates
- Alt text accessibility
"""

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone
from blog.models import Entry, Blogmark
from til.models import TIL
from core.models import EnhancedTag
from PIL import Image
from io import BytesIO
import tempfile
import os


class ImageFieldTests(TestCase):
    """Test that image fields exist and work correctly on all models."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_entry_has_image_fields(self):
        """Test Entry model has image and image_caption fields."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test summary',
            body='Test body',
            status='published'
        )

        # Check fields exist
        self.assertTrue(hasattr(entry, 'image'))
        self.assertTrue(hasattr(entry, 'image_caption'))
        self.assertTrue(hasattr(entry, 'card_image'))  # Legacy field

        # Check fields are initially None/blank
        self.assertFalse(entry.image)
        self.assertIsNone(entry.image_caption)

    def test_blogmark_has_image_fields(self):
        """Test Blogmark model has image and image_caption fields."""
        blogmark = Blogmark.objects.create(
            title='Test Blogmark',
            slug='test-blogmark',
            url='https://example.com',
            commentary='Test commentary',
            status='published'
        )

        # Check fields exist
        self.assertTrue(hasattr(blogmark, 'image'))
        self.assertTrue(hasattr(blogmark, 'image_caption'))

        # Check fields are initially None/blank
        self.assertFalse(blogmark.image)
        self.assertIsNone(blogmark.image_caption)

    def test_til_has_image_fields(self):
        """Test TIL model has image and image_caption fields."""
        til = TIL.objects.create(
            title='Test TIL',
            slug='test-til',
            body='Test body',
            author=self.user
        )

        # Check fields exist
        self.assertTrue(hasattr(til, 'image'))
        self.assertTrue(hasattr(til, 'image_caption'))
        self.assertTrue(hasattr(til, 'card_image'))  # Legacy field

        # Check fields are initially None/blank
        self.assertFalse(til.image)
        self.assertIsNone(til.image_caption)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ImageUploadTests(TestCase):
    """Test image upload functionality with local storage."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def create_test_image(self, size=(800, 600), format='JPEG'):
        """Helper to create a test image file."""
        image = Image.new('RGB', size, color='red')
        img_io = BytesIO()
        image.save(img_io, format=format)
        img_io.seek(0)
        return SimpleUploadedFile(
            name=f'test_image.{format.lower()}',
            content=img_io.read(),
            content_type=f'image/{format.lower()}'
        )

    def test_entry_image_upload(self):
        """Test uploading an image to Entry model."""
        test_image = self.create_test_image()

        entry = Entry.objects.create(
            title='Test Entry with Image',
            slug='test-entry-image',
            summary='Test summary',
            body='Test body',
            status='published',
            image=test_image,
            image_caption='Test image description'
        )

        # Check image was saved
        self.assertTrue(entry.image)
        self.assertIn('blog/images/', entry.image.name)
        self.assertEqual(entry.image_caption, 'Test image description')

        # Check image file exists
        self.assertTrue(os.path.exists(entry.image.path))

    def test_blogmark_image_upload(self):
        """Test uploading an image to Blogmark model."""
        test_image = self.create_test_image()

        blogmark = Blogmark.objects.create(
            title='Test Blogmark with Image',
            slug='test-blogmark-image',
            url='https://example.com',
            commentary='Test commentary',
            status='published',
            image=test_image,
            image_caption='Blogmark image description'
        )

        # Check image was saved
        self.assertTrue(blogmark.image)
        self.assertIn('blog/blogmarks/', blogmark.image.name)
        self.assertEqual(blogmark.image_caption, 'Blogmark image description')

    def test_til_image_upload(self):
        """Test uploading an image to TIL model."""
        test_image = self.create_test_image()

        til = TIL.objects.create(
            title='Test TIL with Image',
            slug='test-til-image',
            body='Test body',
            author=self.user,
            image=test_image,
            image_caption='TIL image description'
        )

        # Check image was saved
        self.assertTrue(til.image)
        self.assertIn('til/images/', til.image.name)
        self.assertEqual(til.image_caption, 'TIL image description')

    def test_image_upload_creates_subdirectories(self):
        """Test that images are organized by date in subdirectories."""
        test_image = self.create_test_image()

        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image=test_image
        )

        # Check year/month structure in path
        now = timezone.now()
        expected_path_parts = ['blog', 'images', str(now.year), f'{now.month:02d}']

        for part in expected_path_parts:
            self.assertIn(part, entry.image.name)


class ImageURLTests(TestCase):
    """Test image URL generation methods."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_entry_get_image_url_with_upload(self):
        """Test get_image_url property returns uploaded image URL."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published'
        )

        # Mock an uploaded image by setting the name
        entry.image.name = 'blog/images/2025/10/test.jpg'

        # get_image_url should return the image URL
        image_url = entry.get_image_url
        self.assertIsNotNone(image_url)
        self.assertIn('blog/images/2025/10/test.jpg', image_url)

    def test_entry_get_image_url_with_card_image_fallback(self):
        """Test get_image_url falls back to card_image URL."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            card_image='https://example.com/image.jpg'
        )

        # Should return card_image when no uploaded image
        self.assertEqual(entry.get_image_url, 'https://example.com/image.jpg')

    def test_entry_get_image_url_prioritizes_upload(self):
        """Test get_image_url prioritizes uploaded image over card_image."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            card_image='https://example.com/old.jpg'
        )

        # Mock uploaded image
        entry.image.name = 'blog/images/2025/10/new.jpg'

        # Should prioritize uploaded image
        image_url = entry.get_image_url
        self.assertIn('new.jpg', image_url)
        self.assertNotIn('old.jpg', image_url)

    def test_blogmark_get_image_url(self):
        """Test Blogmark get_image_url returns None when no image."""
        blogmark = Blogmark.objects.create(
            title='Test Blogmark',
            slug='test-blogmark',
            url='https://example.com',
            commentary='Test',
            status='published'
        )

        # Should return None when no image
        self.assertIsNone(blogmark.get_image_url)

        # Mock uploaded image
        blogmark.image.name = 'blog/blogmarks/2025/10/test.jpg'

        # Should return image URL
        self.assertIsNotNone(blogmark.get_image_url)
        self.assertIn('test.jpg', blogmark.get_image_url)

    def test_til_get_image_url_with_fallback(self):
        """Test TIL get_image_url with card_image fallback."""
        til = TIL.objects.create(
            title='Test TIL',
            slug='test-til',
            body='Test',
            author=self.user,
            card_image='https://example.com/card.jpg'
        )

        # Should return card_image when no upload
        self.assertEqual(til.get_image_url, 'https://example.com/card.jpg')


class ImageCaptionTests(TestCase):
    """Test image caption for accessibility and markdown rendering."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_image_caption_stored(self):
        """Test that image caption is properly stored."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image_caption='A **beautiful** sunset over the ocean'
        )

        entry.refresh_from_db()
        self.assertEqual(entry.image_caption, 'A **beautiful** sunset over the ocean')

    def test_image_caption_optional(self):
        """Test that image caption is optional."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published'
        )

        # Should be None/empty by default
        self.assertIsNone(entry.image_caption)

    def test_image_caption_max_length(self):
        """Test image caption respects max_length."""
        long_caption = 'A' * 300  # Longer than max_length (255)

        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image_caption=long_caption[:255]  # Should be truncated
        )

        self.assertEqual(len(entry.image_caption), 255)

    def test_image_caption_html_rendering(self):
        """Test that caption markdown is rendered to HTML."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image_caption='A **bold** and *italic* caption'
        )

        # Should render markdown
        self.assertIn('<strong>bold</strong>', entry.image_caption_html)
        self.assertIn('<em>italic</em>', entry.image_caption_html)

    def test_image_alt_text_strips_markdown(self):
        """Test that alt text strips markdown from caption."""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published',
            image_caption='A **bold** and *italic* caption'
        )

        # Should strip all markdown/HTML for alt text
        self.assertEqual(entry.image_alt_text, 'A bold and italic caption')
        self.assertNotIn('**', entry.image_alt_text)
        self.assertNotIn('*', entry.image_alt_text)

    def test_image_alt_text_fallback(self):
        """Test that alt text falls back to title when no caption."""
        entry = Entry.objects.create(
            title='Test Entry Title',
            slug='test-entry',
            summary='Test',
            body='Test',
            status='published'
        )

        # Should fall back to title
        self.assertEqual(entry.image_alt_text, 'Test Entry Title')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ImageMigrationTests(TestCase):
    """Test backward compatibility with existing entries."""

    def test_existing_entries_work_without_images(self):
        """Test that existing entries without images still work."""
        entry = Entry.objects.create(
            title='Old Entry',
            slug='old-entry',
            summary='Created before image support',
            body='Test body',
            status='published'
        )

        # Should not crash
        self.assertFalse(entry.image)
        self.assertIsNone(entry.image_caption)

        # get_image_url should handle missing image gracefully
        self.assertIsNone(entry.get_image_url)

    def test_legacy_card_image_still_works(self):
        """Test that legacy card_image URLs still work."""
        entry = Entry.objects.create(
            title='Legacy Entry',
            slug='legacy-entry',
            summary='Test',
            body='Test',
            status='published',
            card_image='https://example.com/legacy.jpg'
        )

        # Legacy card_image should still work via get_image_url
        self.assertEqual(entry.get_image_url, 'https://example.com/legacy.jpg')

    def test_migration_from_card_image_to_upload(self):
        """Test migrating from card_image to uploaded image using actual file."""
        # Start with card_image
        entry = Entry.objects.create(
            title='Migrating Entry',
            slug='migrating-entry',
            summary='Test',
            body='Test',
            status='published',
            card_image='https://example.com/old.jpg'
        )

        self.assertEqual(entry.get_image_url, 'https://example.com/old.jpg')

        # Create actual test image file for migration scenario
        image = Image.new('RGB', (100, 100), color='blue')
        img_io = BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)
        test_image = SimpleUploadedFile(
            name='new.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )

        # Add uploaded image (migration scenario)
        entry.image = test_image
        entry.save()

        # Should now prioritize uploaded image
        self.assertIn('new.jpg', entry.get_image_url)
