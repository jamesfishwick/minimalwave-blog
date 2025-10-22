"""
Tests for image processing utilities.

Tests cover:
- Image optimization (resize, quality, format conversion)
- Thumbnail generation
- RGBA to RGB conversion
- WebP conversion
- File size reduction
"""

from django.test import TestCase
from blog.utils.image_processing import optimize_image, create_thumbnail
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile


class ImageOptimizationTests(TestCase):
    """Test image optimization functionality."""

    def create_test_image(self, size=(2000, 1500), mode='RGB', format='JPEG'):
        """Helper to create a test image."""
        image = Image.new(mode, size, color='red')
        img_io = BytesIO()
        image.save(img_io, format=format)
        img_io.seek(0)
        return SimpleUploadedFile(
            name=f'test_image.{format.lower()}',
            content=img_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )

    def test_optimize_image_resizes_large_images(self):
        """Test that large images are resized to max_width."""
        # Create a large 2000x1500 image
        large_image = self.create_test_image(size=(2000, 1500))
        original_size = len(large_image.read())
        large_image.seek(0)

        # Optimize with max_width=1200
        optimized = optimize_image(large_image, max_width=1200)

        # Read the optimized image
        img = Image.open(optimized)

        # Check dimensions - width should be 1200, height proportional
        self.assertEqual(img.width, 1200)
        self.assertEqual(img.height, 900)  # 1200 * (1500/2000) = 900

        # Check file size is smaller
        optimized.seek(0)
        optimized_size = len(optimized.read())
        self.assertLess(optimized_size, original_size)

    def test_optimize_image_preserves_small_images(self):
        """Test that small images are not upscaled."""
        # Create a small 800x600 image
        small_image = self.create_test_image(size=(800, 600))

        # Optimize with max_width=1200
        optimized = optimize_image(small_image, max_width=1200)

        # Read the optimized image
        img = Image.open(optimized)

        # Dimensions should remain 800x600 (not upscaled)
        self.assertEqual(img.width, 800)
        self.assertEqual(img.height, 600)

    def test_optimize_image_quality_setting(self):
        """Test that quality parameter affects file size."""
        test_image = self.create_test_image(size=(1200, 900))

        # Optimize with high quality
        high_quality = optimize_image(test_image, quality=95)
        high_quality.seek(0)
        high_quality_size = len(high_quality.read())

        # Reset and optimize with low quality
        test_image.seek(0)
        low_quality = optimize_image(test_image, quality=60)
        low_quality.seek(0)
        low_quality_size = len(low_quality.read())

        # Low quality should be smaller
        self.assertLess(low_quality_size, high_quality_size)

    def test_optimize_image_preserves_png_format(self):
        """Test that PNG format is preserved (modern browsers support it)."""
        png_image = self.create_test_image(size=(800, 600), format='PNG')

        # Optimize without conversion
        optimized = optimize_image(png_image, convert_to_webp=False)

        # PNG should be preserved
        self.assertTrue(optimized.name.endswith('.png'))

        # Verify it's actually PNG
        img = Image.open(optimized)
        self.assertEqual(img.format, 'PNG')

    def test_optimize_image_converts_to_webp(self):
        """Test conversion to WebP format."""
        jpeg_image = self.create_test_image(size=(800, 600), format='JPEG')

        # Optimize with WebP conversion
        optimized = optimize_image(jpeg_image, convert_to_webp=True)

        # Check format
        self.assertTrue(optimized.name.endswith('.webp'))

        # Verify it's actually WebP
        img = Image.open(optimized)
        self.assertEqual(img.format, 'WEBP')

    def test_optimize_image_preserves_rgba_in_png(self):
        """Test that RGBA is preserved in PNG (supports transparency)."""
        # Create RGBA image (with transparency)
        rgba_image = self.create_test_image(size=(800, 600), mode='RGBA', format='PNG')

        # Optimize - should preserve PNG with RGBA
        optimized = optimize_image(rgba_image, convert_to_webp=False)

        # Should remain PNG
        self.assertTrue(optimized.name.endswith('.png'))

        # RGBA should be preserved (PNG supports transparency)
        img = Image.open(optimized)
        self.assertEqual(img.mode, 'RGBA')

    def test_optimize_image_jpeg_uses_rgb_mode(self):
        """Test that JPEG format uses RGB mode (no transparency)."""
        # JPEG format always uses RGB
        jpeg_image = self.create_test_image(size=(800, 600), mode='RGB', format='JPEG')
        optimized = optimize_image(jpeg_image, convert_to_webp=False)

        # Should remain JPEG with RGB mode
        self.assertTrue(optimized.name.endswith('.jpg'))
        img = Image.open(optimized)
        self.assertEqual(img.mode, 'RGB')

    def test_optimize_image_preserves_aspect_ratio(self):
        """Test that aspect ratio is preserved during resize."""
        # Create 1600x900 image (16:9 aspect ratio)
        test_image = self.create_test_image(size=(1600, 900))

        # Optimize to 1200px width
        optimized = optimize_image(test_image, max_width=1200)

        img = Image.open(optimized)

        # Calculate aspect ratios
        original_ratio = 1600 / 900
        optimized_ratio = img.width / img.height

        # Should be very close (allow tiny floating point difference)
        self.assertAlmostEqual(original_ratio, optimized_ratio, places=1)

    def test_optimize_image_handles_portrait_orientation(self):
        """Test optimization of portrait-oriented images."""
        # Create portrait image (taller than wide)
        portrait_image = self.create_test_image(size=(900, 1600))

        # Optimize with max_width=1200
        optimized = optimize_image(portrait_image, max_width=1200)

        img = Image.open(optimized)

        # Width should be 900 (not resized since already under max_width)
        self.assertEqual(img.width, 900)
        self.assertEqual(img.height, 1600)


class ThumbnailGenerationTests(TestCase):
    """Test thumbnail generation functionality."""

    def create_test_image(self, size=(800, 600), mode='RGB'):
        """Helper to create a test image."""
        image = Image.new(mode, size, color='blue')
        img_io = BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_create_thumbnail_default_size(self):
        """Test thumbnail creation with default size."""
        test_image = self.create_test_image(size=(1200, 900))

        # Create thumbnail with default size (300x300)
        thumbnail = create_thumbnail(test_image)

        img = Image.open(thumbnail)

        # Should fit within 300x300 while maintaining aspect ratio
        self.assertLessEqual(img.width, 300)
        self.assertLessEqual(img.height, 300)

    def test_create_thumbnail_custom_size(self):
        """Test thumbnail creation with custom size."""
        test_image = self.create_test_image(size=(1200, 900))

        # Create thumbnail with custom size
        thumbnail = create_thumbnail(test_image, size=(150, 150))

        img = Image.open(thumbnail)

        # Should fit within 150x150
        self.assertLessEqual(img.width, 150)
        self.assertLessEqual(img.height, 150)

    def test_create_thumbnail_maintains_aspect_ratio(self):
        """Test that thumbnails maintain aspect ratio."""
        # Create 16:9 image
        test_image = self.create_test_image(size=(1600, 900))

        thumbnail = create_thumbnail(test_image, size=(300, 300))

        img = Image.open(thumbnail)

        # Calculate aspect ratios
        original_ratio = 1600 / 900
        thumb_ratio = img.width / img.height

        # Should be very close
        self.assertAlmostEqual(original_ratio, thumb_ratio, places=1)

    def test_create_thumbnail_converts_rgba_to_rgb(self):
        """Test RGBA to RGB conversion for thumbnails."""
        # Create RGBA image
        rgba_img = Image.new('RGBA', (800, 600), color='blue')
        img_io = BytesIO()
        rgba_img.save(img_io, format='PNG')
        img_io.seek(0)

        rgba_image = SimpleUploadedFile(
            name='test_image.png',
            content=img_io.getvalue(),
            content_type='image/png'
        )

        # Create thumbnail
        thumbnail = create_thumbnail(rgba_image)

        img = Image.open(thumbnail)

        # Should be RGB, not RGBA
        self.assertEqual(img.mode, 'RGB')

    def test_create_thumbnail_filename(self):
        """Test that thumbnail has correct filename suffix."""
        test_image = self.create_test_image()

        thumbnail = create_thumbnail(test_image)

        # Should have _thumb suffix
        self.assertTrue(thumbnail.name.endswith('_thumb.jpg'))

    def test_create_thumbnail_smaller_than_original(self):
        """Test that thumbnail file size is smaller than original."""
        test_image = self.create_test_image(size=(2000, 1500))
        original_size = len(test_image.read())
        test_image.seek(0)

        thumbnail = create_thumbnail(test_image)
        thumbnail.seek(0)
        thumbnail_size = len(thumbnail.read())

        # Thumbnail should be much smaller
        self.assertLess(thumbnail_size, original_size)


class ImageProcessingEdgeCasesTests(TestCase):
    """Test edge cases and error handling."""

    def test_optimize_very_small_image(self):
        """Test optimizing a very small image."""
        # Create tiny 50x50 image
        tiny_img = Image.new('RGB', (50, 50), color='green')
        img_io = BytesIO()
        tiny_img.save(img_io, format='JPEG')
        img_io.seek(0)

        tiny_image = SimpleUploadedFile(
            name='tiny.jpg',
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

        # Should not fail
        optimized = optimize_image(tiny_image, max_width=1200)

        img = Image.open(optimized)
        # Should remain 50x50
        self.assertEqual(img.width, 50)
        self.assertEqual(img.height, 50)

    def test_optimize_square_image(self):
        """Test optimizing a square image."""
        square_img = Image.new('RGB', (1000, 1000), color='yellow')
        img_io = BytesIO()
        square_img.save(img_io, format='JPEG')
        img_io.seek(0)

        square_image = SimpleUploadedFile(
            name='square.jpg',
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

        optimized = optimize_image(square_image, max_width=800)

        img = Image.open(optimized)
        # Should be 800x800 (square maintained)
        self.assertEqual(img.width, 800)
        self.assertEqual(img.height, 800)

    def test_create_thumbnail_portrait_image(self):
        """Test thumbnail of portrait-oriented image."""
        portrait_img = Image.new('RGB', (600, 1200), color='purple')
        img_io = BytesIO()
        portrait_img.save(img_io, format='JPEG')
        img_io.seek(0)

        portrait_image = SimpleUploadedFile(
            name='portrait.jpg',
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

        thumbnail = create_thumbnail(portrait_image, size=(300, 300))

        img = Image.open(thumbnail)

        # Width should be proportional to fit within 300x300
        self.assertLessEqual(img.width, 300)
        self.assertLessEqual(img.height, 300)
        # Height should be the limiting dimension for portrait
        self.assertEqual(img.height, 300)
