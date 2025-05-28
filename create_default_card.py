import os
from PIL import Image, ImageDraw, ImageFont
import io

# Create a default social media card image with minimal wave aesthetics
width, height = 1200, 630
background_color = (18, 18, 18)  # Dark background
accent_color = (255, 0, 255)     # Magenta
accent_color2 = (0, 255, 255)    # Cyan

# Create a new image with dark background
image = Image.new('RGB', (width, height), background_color)
draw = ImageDraw.Draw(image)

# Draw a grid pattern (minimal wave aesthetic)
grid_spacing = 40
for x in range(0, width, grid_spacing):
    draw.line([(x, 0), (x, height)], fill=(30, 30, 30), width=1)
for y in range(0, height, grid_spacing):
    draw.line([(0, y), (width, y)], fill=(30, 30, 30), width=1)

# Draw diagonal lines for a retro feel
draw.line([(0, 0), (width, height)], fill=accent_color, width=3)
draw.line([(0, height), (width, 0)], fill=accent_color2, width=3)

# Draw a border
border_width = 10
draw.rectangle([(0, 0), (width-1, height-1)], outline=accent_color, width=border_width)

# Add text
try:
    # Try to use a system font
    font_large = ImageFont.truetype("Arial", 80)
    font_small = ImageFont.truetype("Arial", 40)
except IOError:
    # Fall back to default font
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Add blog title
title_text = "MINIMAL WAVE BLOG"
draw.text((width//2, height//2 - 50), title_text, fill=accent_color, font=font_large, anchor="mm")

# Add tagline
tagline_text = "Dark Mode • Minimal Aesthetics"
draw.text((width//2, height//2 + 50), tagline_text, fill=accent_color2, font=font_small, anchor="mm")

# Save the image
image.save('/home/ubuntu/minimalwave-blog/static/images/default-card.jpg', quality=95)
print("Default social media card image created successfully.")
