# Automatic Content Tagging with AI

This document explains how to use the AI-powered auto-tagging system to automatically generate and apply relevant tags to your blog content.

## Overview

The `auto_tag_content` management command uses Claude AI (Anthropic's API) to analyze your blog posts, TIL entries, and blogmarks to generate semantically relevant tags that are optimized for SEO and content discovery.

### Features

- **AI-Powered Analysis**: Uses Claude 3.5 Sonnet to understand content and extract meaningful topics
- **SEO Optimization**: Generates tags that improve discoverability and search rankings
- **Smart Tag Generation**: Creates 3-7 specific, relevant tags per post (configurable)
- **Automatic Tag Creation**: Creates new tags as needed and reuses existing ones
- **Multi-Content Support**: Works with Blog Entries, Blogmarks, and TIL posts
- **Safe Testing**: Dry-run mode to preview tags before applying them
- **Selective Processing**: Options to filter by content type, limit processing, or force re-tagging

## Setup

### 1. Install Dependencies

The Anthropic SDK is already included in the project dependencies. If you need to install it manually:

```bash
# In Docker
docker exec minimalwave-blog-container poetry add anthropic

# Locally
poetry add anthropic
```

### 2. Configure API Key

You need an Anthropic API key to use this feature:

1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Add it to your `.env` file:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

3. Restart your Docker container to load the new environment variable:

```bash
docker restart minimalwave-blog-container
```

## Usage

### Basic Usage

Generate tags for all untagged content:

```bash
# In Docker (recommended)
docker exec minimalwave-blog-container python manage.py auto_tag_content

# Locally
python manage.py auto_tag_content
```

### Dry Run (Preview Mode)

See what tags would be generated without making any changes:

```bash
docker exec minimalwave-blog-container python manage.py auto_tag_content --dry-run
```

**Output example:**
```
DRY RUN MODE - No changes will be made

Processing 2 blog entries...

  Blog Entry: Test Entry with Crab Rave
    Current tags: Test Tag
    Would apply: test, images, media-upload, gif, web-development

  Blog Entry: test test test
    Would apply: artificial-intelligence, ai-safety, ethics, nonprofit, technology

============================================================
SUMMARY
============================================================
Processed: 2
Tagged: 2
Skipped: 0
```

### Advanced Options

#### Force Re-tag Existing Content

Re-generate tags for content that already has tags:

```bash
docker exec minimalwave-blog-container python manage.py auto_tag_content --force
```

#### Process Specific Content Type

Only tag blog entries, blogmarks, or TIL posts:

```bash
# Only blog entries
docker exec minimalwave-blog-container python manage.py auto_tag_content --content-type entry

# Only TIL posts
docker exec minimalwave-blog-container python manage.py auto_tag_content --content-type til

# Only blogmarks
docker exec minimalwave-blog-container python manage.py auto_tag_content --content-type blogmark
```

#### Limit Processing

Process only a specific number of items (useful for testing):

```bash
# Process only the 5 most recent posts
docker exec minimalwave-blog-container python manage.py auto_tag_content --limit 5
```

#### Custom Tag Count

Control the number of tags generated per post:

```bash
# Generate 5-10 tags per post
docker exec minimalwave-blog-container python manage.py auto_tag_content --min-tags 5 --max-tags 10

# Generate exactly 3 tags per post
docker exec minimalwave-blog-container python manage.py auto_tag_content --min-tags 3 --max-tags 3
```

#### Combine Options

You can combine multiple options:

```bash
# Dry run on the 3 most recent blog entries, forcing re-tag, with 4-6 tags each
docker exec minimalwave-blog-container python manage.py auto_tag_content \
  --dry-run \
  --force \
  --content-type entry \
  --limit 3 \
  --min-tags 4 \
  --max-tags 6
```

## How It Works

### Tag Generation Process

1. **Content Analysis**: The command extracts the title and body of each post
2. **AI Processing**: Sends the content to Claude AI with specific instructions to:
   - Identify main topics and themes
   - Extract technical concepts, tools, frameworks mentioned
   - Consider SEO value and discoverability
   - Generate specific, meaningful tags (not generic ones)
3. **Tag Normalization**: Cleans and formats tags (lowercase, hyphenated)
4. **Database Operations**: Creates new tags if needed or reuses existing ones
5. **Application**: Applies tags to the content

### Tag Quality Guidelines

The AI is instructed to generate tags that are:

- **Semantically relevant**: Actually related to the content's main topics
- **SEO-optimized**: Improve search discoverability
- **Specific**: Avoid generic tags like "technology" or "programming"
- **Properly formatted**: Lowercase, hyphenated for multi-word tags
- **Technical**: Focus on tools, frameworks, concepts, industries

### Example Tag Transformations

| Content About | Generated Tags |
|--------------|----------------|
| Django REST API tutorial | `python`, `django`, `rest-api`, `web-development`, `backend` |
| React performance tips | `react`, `javascript`, `performance`, `optimization`, `frontend` |
| Machine learning basics | `machine-learning`, `python`, `data-science`, `artificial-intelligence` |
| Docker deployment guide | `docker`, `devops`, `deployment`, `containers`, `infrastructure` |

## Best Practices

### When to Use

- **Initial Setup**: Tag all existing content when first setting up the blog
- **Bulk Tagging**: After importing content from another platform
- **Periodic Maintenance**: Re-tag content with `--force` if tag quality improves over time
- **New Content**: Can be used on individual new posts, but manual tagging during creation may be more efficient

### When NOT to Use

- **Production Deployments**: Don't run this during deployments (API calls take time)
- **Without Testing**: Always do a `--dry-run` first to verify tag quality
- **Without API Key**: The command will fail without a valid ANTHROPIC_API_KEY

### Cost Considerations

Each post requires one API call to Claude. Anthropic pricing (as of 2024):
- Claude 3.5 Sonnet: ~$0.003 per request (for typical blog post length)
- 100 posts ≈ $0.30
- 1,000 posts ≈ $3.00

The command uses a lower temperature (0.3) for consistent, deterministic tagging.

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable not set"

**Solution**: Add your API key to `.env` and restart the Docker container.

### "No tags generated for entry"

**Possible causes**:
- Content is too short or lacks substance
- API rate limiting
- Network issues

**Solution**: Check the error message, verify API key, try again with `--limit 1` to debug.

### Tags seem too generic

**Solution**: The AI is designed to avoid generic tags, but if you see them:
1. Report the issue with example content
2. Consider adjusting the prompt in `blog/management/commands/auto_tag_content.py`

### Tags are too specific/obscure

**Solution**: Adjust `--min-tags` and `--max-tags` to get broader coverage.

## Maintenance

### Viewing Generated Tags

Check tags in the Django admin:
- URL: `http://localhost:8000/admin/core/enhancedtag/`
- View usage counts, featured tags, and active/inactive status

### Managing Tags

- **Edit tag names**: Use Django admin to rename tags
- **Merge tags**: Manually reassign content in admin, then delete duplicate
- **Delete unused tags**: Django admin shows usage counts

### Re-running on Updates

If you update existing posts with significant new content, re-run with `--force`:

```bash
docker exec minimalwave-blog-container python manage.py auto_tag_content --force --content-type entry --limit 1
```

## Integration with Workflows

### Pre-Publication Checklist

Before publishing a post, you can:

1. Write your content in admin (leave tags empty)
2. Run auto-tagging: `python manage.py auto_tag_content --content-type entry --limit 1`
3. Review and adjust tags in admin
4. Publish

### Scheduled Tagging

For automated workflows, you could add a cron job or CI/CD step:

```bash
# Weekly re-tag of recent untagged content
0 2 * * 0 docker exec minimalwave-blog-container python manage.py auto_tag_content --limit 10
```

## Future Enhancements

Potential improvements for this feature:

- **Tag suggestions in admin**: Show AI-suggested tags when creating/editing posts
- **Tag hierarchy**: Group related tags (e.g., "python" parent of "django")
- **Trending tags**: Track which tags drive the most traffic
- **Related posts**: Use tags to suggest related content
- **Tag analytics**: Show which tags perform best for SEO

## Support

If you encounter issues or have suggestions:

1. Check this documentation
2. Review the command help: `python manage.py auto_tag_content --help`
3. Check Django logs for errors
4. Verify your ANTHROPIC_API_KEY is valid
