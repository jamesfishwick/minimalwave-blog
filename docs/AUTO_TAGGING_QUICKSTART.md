# Auto-Tagging Quick Start Guide

## Setup (One-Time)

1. **Get an Anthropic API key**
   - Visit: https://console.anthropic.com/
   - Create an account and generate an API key
   - Copy the key (starts with `sk-ant-api03-...`)

2. **Add to your .env file**
   ```bash
   # Add this line to your .env file
   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
   ```

3. **Restart Docker**
   ```bash
   docker restart minimalwave-blog-container
   ```

## Usage

### Preview Tags (Safe - No Changes)
```bash
docker exec minimalwave-blog-container python manage.py auto_tag_content --dry-run
```

### Apply Tags to Untagged Content
```bash
docker exec minimalwave-blog-container python manage.py auto_tag_content
```

### Re-tag Everything (Including Already Tagged)
```bash
docker exec minimalwave-blog-container python manage.py auto_tag_content --force
```

### Tag Only Recent Posts
```bash
docker exec minimalwave-blog-container python manage.py auto_tag_content --limit 5
```

### Tag Only Blog Entries
```bash
docker exec minimalwave-blog-container python manage.py auto_tag_content --content-type entry
```

## What You'll See

```
Processing 2 blog entries...

  Blog Entry: Test Entry with Crab Rave
    Current tags: Test Tag
    Applying: test, images, media-upload, gif, web-development
      Created new tag: images
      Created new tag: media-upload
      Created new tag: gif
      Created new tag: web-development

  Blog Entry: test test test
    Applying: artificial-intelligence, ai-safety, ethics, nonprofit
      Created new tag: artificial-intelligence
      Created new tag: ai-safety
      Created new tag: ethics
      Created new tag: nonprofit

============================================================
SUMMARY
============================================================
Processed: 2
Tagged: 2
Skipped: 0
```

## Common Workflows

### Initial Blog Setup
```bash
# 1. Preview what will happen
docker exec minimalwave-blog-container python manage.py auto_tag_content --dry-run

# 2. Apply tags
docker exec minimalwave-blog-container python manage.py auto_tag_content

# 3. Review in admin: http://localhost:8000/admin/core/enhancedtag/
```

### Periodic Maintenance
```bash
# Re-tag recent content (last 10 posts)
docker exec minimalwave-blog-container python manage.py auto_tag_content --force --limit 10
```

### Before Publishing a New Post
```bash
# Tag just the newest entry
docker exec minimalwave-blog-container python manage.py auto_tag_content --content-type entry --limit 1
```

## Troubleshooting

**"ANTHROPIC_API_KEY environment variable not set"**
- Add the key to your `.env` file
- Restart Docker: `docker restart minimalwave-blog-container`

**Tags seem wrong or irrelevant**
- Use `--dry-run` first to preview
- Tags are AI-generated; review and adjust in admin if needed
- Report consistent issues for prompt improvements

**Want different number of tags?**
```bash
# Generate 5-8 tags per post instead of default 3-7
docker exec minimalwave-blog-container python manage.py auto_tag_content --min-tags 5 --max-tags 8
```

## Cost

Anthropic Claude API pricing (approximate):
- ~$0.003 per blog post
- 100 posts ≈ $0.30
- 1,000 posts ≈ $3.00

Very affordable for automated tagging!

## Full Documentation

For complete details, see: `docs/AUTO_TAGGING.md`
