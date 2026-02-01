# Markdown Image Placement Guide

This guide explains how to insert and position images in your blog content using enhanced markdown syntax.

## Quick Start

### For Content Editors (Simple Syntax)

Use shortcodes for quick image insertion:

```markdown
{{img:uploads/my-photo.jpg|right|300|My photo caption}}
```

### For Power Users (Full Control)

Use markdown attributes for complete flexibility:

```markdown
![My photo caption](uploads/my-photo.jpg){: .align-right .w-300}
```

---

## Method 1: Shortcode Syntax (Recommended for Most Users)

### Basic Syntax

```
{{img:path|position|width|caption}}
```

### Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `path` | Yes | File path or URL | Image location (see Path Examples below) |
| `position` | Yes | `left`, `right`, `center`, `full` | Where to place the image |
| `width` | Yes | `200`, `300`, `400`, `500`, `800` | Maximum width in pixels |
| `caption` | No | Any text | Becomes both alt text and visible caption |

### Path Examples

**Local uploaded images** (automatically prepends `/media/`):
```markdown
{{img:uploads/photo.jpg|right|300}}
{{img:blog/images/2026/01/sunset.jpg|center|800}}
```

**External images** (absolute URLs):
```markdown
{{img:https://example.com/image.jpg|center|500|External image}}
```

### Position Examples

**Float right** (text wraps on the left):
```markdown
{{img:uploads/sidebar.jpg|right|300|Sidebar image}}

This text will wrap around the left side of the image.
```

**Float left** (text wraps on the right):
```markdown
{{img:uploads/thumbnail.jpg|left|200|Small thumbnail}}

This text will wrap around the right side of the image.
```

**Center aligned** (full width of content):
```markdown
{{img:uploads/hero.jpg|center|800|Hero image}}

This appears below the centered image.
```

**Full width** (100% of container):
```markdown
{{img:uploads/banner.jpg|full|1200|Full width banner}}
```

### Complete Examples

**With caption:**
```markdown
{{img:uploads/sunset.jpg|right|400|Golden hour over the mountains}}

Lorem ipsum dolor sit amet, consectetur adipiscing elit. The text
wraps nicely around the floated image on the right.
```

**Without caption:**
```markdown
{{img:uploads/logo.png|center|200}}

A centered logo without any caption text.
```

**Multiple images:**
```markdown
{{img:uploads/photo1.jpg|left|300|First photo}}

Some text here describing both photos.

{{img:uploads/photo2.jpg|right|300|Second photo}}

More descriptive text continues here.
```

---

## Method 2: Markdown Attributes (For Advanced Users)

### Basic Syntax

```markdown
![Alt text](path/to/image.jpg){: .class1 .class2}
```

### Available CSS Classes

**Alignment classes:**
- `.align-left` - Float image to the left
- `.align-right` - Float image to the right
- `.align-center` - Center the image

**Width classes:**
- `.w-200` - Maximum width 200px
- `.w-300` - Maximum width 300px
- `.w-400` - Maximum width 400px
- `.w-500` - Maximum width 500px
- `.w-800` - Maximum width 800px
- `.full-width` - 100% width

### Examples

**Single class:**
```markdown
![My photo](uploads/photo.jpg){: .align-right}
![Hero image](uploads/hero.jpg){: .full-width}
```

**Multiple classes:**
```markdown
![Thumbnail](uploads/thumb.jpg){: .align-left .w-200}
![Banner](uploads/banner.jpg){: .align-center .w-800}
```

**Inline styles:**
```markdown
![Custom](uploads/image.jpg){: style="max-width: 350px; border-radius: 10px;"}
```

**Combining classes and styles:**
```markdown
![Photo](uploads/photo.jpg){: .align-right style="max-width: 450px;"}
```

---

## Output HTML (What Gets Generated)

### Shortcode Output

Input:
```markdown
{{img:uploads/sunset.jpg|right|400|Beautiful sunset}}
```

Output:
```html
<figure class="markdown-image float-right" style="max-width: 400px;">
    <img src="/media/uploads/sunset.jpg" alt="Beautiful sunset" loading="lazy">
    <figcaption>Beautiful sunset</figcaption>
</figure>
```

### Attribute Output

Input:
```markdown
![Beautiful sunset](uploads/sunset.jpg){: .align-right .w-400}
```

Output:
```html
<p><img src="uploads/sunset.jpg" alt="Beautiful sunset" class="align-right w-400"></p>
```

---

## Mobile Behavior

**On desktop** (≥ 768px width):
- Floated images appear alongside text
- Images respect specified width constraints

**On mobile** (< 768px width):
- All floated images automatically stack (no floating)
- Images become full-width for better readability
- Vertical spacing is maintained

---

## Accessibility Features

Both methods produce accessible HTML:

✅ **Semantic HTML** - Uses `<figure>` and `<figcaption>` (shortcode method)
✅ **Alt text** - Caption becomes alt text for screen readers
✅ **Lazy loading** - Images use `loading="lazy"` for performance
✅ **Color contrast** - Figcaption color meets WCAG AA standards
✅ **Keyboard navigation** - All images are properly focusable
✅ **Screen reader friendly** - Semantic structure is announced correctly

---

## Tips and Best Practices

### Choosing Width Values

- **200px** - Small thumbnails, icons, profile pictures
- **300px** - Medium thumbnails, sidebar images
- **400px** - Standard content images
- **500px** - Large content images
- **800px** - Hero images, feature graphics
- **full** - Banners, wide screenshots

### Caption Guidelines

✅ **Do:**
- Keep captions concise (1-2 sentences)
- Describe what's important about the image
- Add context that isn't obvious from the image

❌ **Don't:**
- Duplicate information already in the text
- Write extremely long captions
- Include decorative text like "Image showing..."

### Performance Tips

- Use appropriate width values (don't use 800px for a 200px space)
- Compress images before uploading
- Use lazy loading (automatic with shortcode syntax)
- Consider using WebP format for better compression

---

## Troubleshooting

### Image Not Showing

**Problem:** Image path is incorrect

**Solution:** Check that the path is relative to `/media/` or use absolute URL:
```markdown
✅ {{img:uploads/photo.jpg|center|400}}
✅ {{img:https://example.com/photo.jpg|center|400}}
❌ {{img:/Users/me/photo.jpg|center|400}}  # Absolute local path won't work
```

### Caption Not Appearing

**Problem:** Missing caption parameter or trailing pipe

**Solution:** Ensure caption text is provided:
```markdown
✅ {{img:photo.jpg|center|400|My caption}}
❌ {{img:photo.jpg|center|400|}}  # Empty caption
```

### Image Not Floating

**Problem:** Incorrect position value

**Solution:** Use only: `left`, `right`, `center`, or `full`:
```markdown
✅ {{img:photo.jpg|left|300}}
❌ {{img:photo.jpg|float-left|300}}  # Wrong value
```

### Syntax Not Processing

**Problem:** Typo in shortcode syntax

**Solution:** Check for:
- Double curly braces `{{` and `}}`
- Proper pipe separators `|`
- No spaces around pipes
- Correct parameter order

```markdown
✅ {{img:photo.jpg|right|300}}
❌ { img:photo.jpg|right|300 }  # Single braces
❌ {{img: photo.jpg | right | 300}}  # Extra spaces
❌ {{img:right|photo.jpg|300}}  # Wrong parameter order
```

---

## Technical Details

### Implementation

The shortcode preprocessing happens in `blog/templatetags/markdown_extras.py` before markdown rendering. The function:

1. Uses regex to find `{{img:...}}` patterns
2. Extracts parameters (path, position, width, caption)
3. Escapes all user input for XSS protection
4. Generates semantic HTML with proper attributes
5. Replaces the shortcode with the generated HTML

### Security

- All user input is HTML-escaped using Python's `html.escape()`
- No raw HTML injection is possible
- Paths are validated and sanitized
- XSS attacks are prevented automatically

### Markdown Extensions Used

The `attr_list` extension is enabled in `minimalwave-blog/settings/base.py`:

```python
MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',      # Tables, footnotes, etc.
    'markdown.extensions.codehilite',  # Syntax highlighting
    'markdown.extensions.attr_list',   # HTML attributes
]
```

---

## Examples Gallery

### Blog Post with Sidebar Image

```markdown
# My Blog Post Title

{{img:uploads/author.jpg|right|300|Photo of the author}}

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
The author photo appears on the right side of this text.
Pellentesque habitant morbi tristique senectus et netus
et malesuada fames ac turpis egestas.

More content continues here...
```

### Article with Hero Image

```markdown
# Breaking News Article

{{img:uploads/hero-news.jpg|center|800|Scene from earlier today}}

The story begins here with the hero image centered above.

Rest of the article content follows...
```

### Tutorial with Multiple Images

```markdown
# Step-by-Step Tutorial

## Step 1: Setup

{{img:uploads/step1.jpg|left|300|Initial setup screen}}

Follow these instructions for the initial setup. The screenshot
on the left shows what you should see.

## Step 2: Configuration

{{img:uploads/step2.jpg|right|300|Configuration panel}}

Now configure the settings as shown in the screenshot to the right.
```

---

## Need Help?

- Check the [CLAUDE.md](../CLAUDE.md) file for developer documentation
- Review the implementation in `blog/templatetags/markdown_extras.py`
- Check CSS styling in `static/css/style.css` (search for "Markdown Image Placement")
- See examples in existing blog posts via the admin interface
