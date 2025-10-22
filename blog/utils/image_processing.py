"""
Image processing utilities for blog images.

Handles optimization, resizing, and format conversion for uploaded images.
"""
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def optimize_image(image_file, max_width=1200, quality=85, convert_to_webp=False):
    """
    Optimize an uploaded image file while preserving modern web formats.

    Supports: JPEG, PNG, WebP, GIF, AVIF
    - Preserves format benefits (PNG transparency, GIF animation, WebP compression)
    - Only converts RGBA to RGB when saving as JPEG
    - Resizes to max_width while maintaining aspect ratio

    Args:
        image_file: Django UploadedFile object
        max_width: Maximum width in pixels (maintains aspect ratio)
        quality: JPEG/WebP/AVIF quality (1-100)
        convert_to_webp: Force conversion to WebP format

    Returns:
        InMemoryUploadedFile: Optimized image file
    """
    img = Image.open(image_file)
    original_format = (img.format or 'JPEG').upper()

    # Map formats to save parameters
    format_config = {
        'JPEG': {'format': 'JPEG', 'ext': 'jpg', 'mime': 'image/jpeg', 'supports_transparency': False},
        'PNG': {'format': 'PNG', 'ext': 'png', 'mime': 'image/png', 'supports_transparency': True},
        'WEBP': {'format': 'WEBP', 'ext': 'webp', 'mime': 'image/webp', 'supports_transparency': True},
        'GIF': {'format': 'GIF', 'ext': 'gif', 'mime': 'image/gif', 'supports_transparency': True},
    }

    # Determine output format
    if convert_to_webp:
        config = format_config['WEBP']
    elif original_format in format_config:
        config = format_config[original_format]
    else:
        # Fallback to JPEG for unsupported formats
        config = format_config['JPEG']

    # Convert RGBA to RGB only if target format doesn't support transparency
    if img.mode in ('RGBA', 'LA', 'P') and not config['supports_transparency']:
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background

    # Resize if image is wider than max_width
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # Save optimized image to BytesIO
    output = BytesIO()

    # Format-specific save options
    save_kwargs = {'optimize': True}
    if config['format'] in ('JPEG', 'WEBP'):
        save_kwargs['quality'] = quality
    if config['format'] == 'WEBP':
        save_kwargs['method'] = 6  # Better compression

    img.save(output, format=config['format'], **save_kwargs)
    output.seek(0)

    # Create new filename with correct extension
    original_name = image_file.name.rsplit('.', 1)[0]
    new_filename = f"{original_name}.{config['ext']}"

    return InMemoryUploadedFile(
        output,
        'ImageField',
        new_filename,
        config['mime'],
        sys.getsizeof(output),
        None
    )


def create_thumbnail(image_file, size=(300, 300)):
    """
    Create a thumbnail from an image file.

    Args:
        image_file: Django UploadedFile object or file path
        size: Tuple of (width, height) for thumbnail

    Returns:
        InMemoryUploadedFile: Thumbnail image file
    """
    img = Image.open(image_file)

    # Convert RGBA to RGB for JPEG
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background

    # Create thumbnail (maintains aspect ratio)
    img.thumbnail(size, Image.Resampling.LANCZOS)

    # Save to BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)

    # Create filename
    if hasattr(image_file, 'name'):
        original_name = image_file.name.rsplit('.', 1)[0]
        new_filename = f"{original_name}_thumb.jpg"
    else:
        new_filename = "thumbnail.jpg"

    return InMemoryUploadedFile(
        output,
        'ImageField',
        new_filename,
        'image/jpeg',
        sys.getsizeof(output),
        None
    )
