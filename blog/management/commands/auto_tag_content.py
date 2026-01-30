"""
Management command to automatically generate and apply tags to blog content using AI.

This command analyzes blog entries and TIL posts, generates semantically relevant tags
optimized for SEO and discovery, and applies them automatically.

Usage:
    python manage.py auto_tag_content [options]

Options:
    --dry-run          Show what tags would be generated without applying them
    --force            Re-tag content that already has tags
    --content-type     Only process specific content type: 'entry', 'blogmark', or 'til'
    --limit N          Only process N items (useful for testing)
    --min-tags N       Minimum number of tags to generate (default: 3)
    --max-tags N       Maximum number of tags to generate (default: 7)
"""

import os
from typing import List, Dict, Any

import anthropic
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from blog.models import Entry, Blogmark
from core.models import EnhancedTag
from til.models import TIL


class Command(BaseCommand):
    help = "Automatically generate and apply tags to blog content using AI"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-tag content that already has tags",
        )
        parser.add_argument(
            "--content-type",
            type=str,
            choices=["entry", "blogmark", "til"],
            help="Only process specific content type",
        )
        parser.add_argument(
            "--limit", type=int, help="Only process N items (useful for testing)"
        )
        parser.add_argument(
            "--min-tags",
            type=int,
            default=3,
            help="Minimum number of tags to generate (default: 3)",
        )
        parser.add_argument(
            "--max-tags",
            type=int,
            default=7,
            help="Maximum number of tags to generate (default: 7)",
        )

    def handle(self, *args, **options):
        # Validate API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise CommandError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please add it to your .env file."
            )

        self.dry_run = options["dry_run"]
        self.force = options["force"]
        self.min_tags = options["min_tags"]
        self.max_tags = options["max_tags"]
        self.client = anthropic.Anthropic(api_key=api_key)

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made\n")
            )

        # Process content based on type
        content_type = options.get("content_type")
        limit = options.get("limit")

        stats = {"processed": 0, "tagged": 0, "skipped": 0, "errors": 0}

        if content_type in [None, "entry"]:
            self._process_entries(limit, stats)

        if content_type in [None, "blogmark"]:
            self._process_blogmarks(limit, stats)

        if content_type in [None, "til"]:
            self._process_tils(limit, stats)

        # Print summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Processed: {stats['processed']}")
        self.stdout.write(self.style.SUCCESS(f"Tagged: {stats['tagged']}"))
        self.stdout.write(self.style.WARNING(f"Skipped: {stats['skipped']}"))
        if stats["errors"] > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {stats['errors']}"))

    def _process_entries(self, limit, stats):
        """Process blog entries"""
        queryset = Entry.objects.all().order_by("-created")
        if limit:
            queryset = queryset[:limit]

        self.stdout.write(f"\nProcessing {queryset.count()} blog entries...")
        for entry in queryset:
            self._process_content(
                entry,
                content_type="Blog Entry",
                title=entry.title,
                body=entry.body,
                stats=stats,
            )

    def _process_blogmarks(self, limit, stats):
        """Process blogmarks"""
        queryset = Blogmark.objects.all().order_by("-created")
        if limit:
            queryset = queryset[:limit]

        if queryset.count() > 0:
            self.stdout.write(f"\nProcessing {queryset.count()} blogmarks...")
            for blogmark in queryset:
                # Blogmarks have link and commentary
                content = f"{blogmark.commentary}\n\nLink: {blogmark.link}"
                self._process_content(
                    blogmark,
                    content_type="Blogmark",
                    title=blogmark.title,
                    body=content,
                    stats=stats,
                )

    def _process_tils(self, limit, stats):
        """Process TIL posts"""
        queryset = TIL.objects.all().order_by("-created")
        if limit:
            queryset = queryset[:limit]

        if queryset.count() > 0:
            self.stdout.write(f"\nProcessing {queryset.count()} TIL posts...")
            for til in queryset:
                self._process_content(
                    til,
                    content_type="TIL",
                    title=til.title,
                    body=til.body,
                    stats=stats,
                )

    def _process_content(self, content_obj, content_type, title, body, stats):
        """Process a single content item"""
        stats["processed"] += 1

        # Skip if already tagged (unless force is set)
        existing_tag_count = content_obj.tags.count()
        if existing_tag_count > 0 and not self.force:
            self.stdout.write(
                f"  Skipping {content_type}: '{title}' (already has {existing_tag_count} tags)"
            )
            stats["skipped"] += 1
            return

        try:
            # Generate tags using AI
            tag_suggestions = self._generate_tags(title, body, content_type)

            if not tag_suggestions:
                self.stdout.write(
                    self.style.WARNING(
                        f"  No tags generated for {content_type}: '{title}'"
                    )
                )
                stats["skipped"] += 1
                return

            # Display what will be done
            self.stdout.write(f"\n  {content_type}: {title}")
            if existing_tag_count > 0:
                current_tags = ", ".join(content_obj.tags.values_list("name", flat=True))
                self.stdout.write(f"    Current tags: {current_tags}")
            self.stdout.write(
                f"    {'Would apply' if self.dry_run else 'Applying'}: {', '.join(tag_suggestions)}"
            )

            # Apply tags if not dry run
            if not self.dry_run:
                self._apply_tags(content_obj, tag_suggestions)
                stats["tagged"] += 1
            else:
                stats["tagged"] += 1  # Count as would-be tagged in dry run

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"  Error processing {content_type} '{title}': {str(e)}"
                )
            )
            stats["errors"] += 1

    def _generate_tags(self, title: str, body: str, content_type: str) -> List[str]:
        """
        Use Claude API to generate relevant tags for content.

        Args:
            title: Content title
            body: Content body (may contain markdown)
            content_type: Type of content (Blog Entry, Blogmark, TIL)

        Returns:
            List of tag names
        """
        # Truncate body if too long (keep first 2000 chars)
        truncated_body = body[:2000] + ("..." if len(body) > 2000 else "")

        prompt = f"""Analyze this {content_type.lower()} post and generate {self.min_tags}-{self.max_tags} relevant tags.

Title: {title}

Content:
{truncated_body}

Generate tags that are:
1. Semantically relevant to the content's main topics
2. Optimized for SEO and content discovery
3. Specific enough to be meaningful (avoid generic tags like "technology" or "programming")
4. Consistent with common tagging conventions (lowercase, hyphenated if multi-word)
5. Focused on technical topics, tools, frameworks, concepts, or industries mentioned

Return ONLY a comma-separated list of tag names, nothing else.
Example: python, django, web-development, rest-api, authentication

Tags:"""

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Using Haiku - faster and cheaper for tagging
                max_tokens=200,
                temperature=0.3,  # Lower temperature for more consistent tagging
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract tags from response
            response_text = message.content[0].text.strip()
            tags = [tag.strip().lower() for tag in response_text.split(",")]

            # Clean and validate tags
            tags = [self._clean_tag(tag) for tag in tags if tag]
            tags = [tag for tag in tags if tag and len(tag) <= 50]  # Max length check

            # Respect min/max limits
            tags = tags[: self.max_tags]
            if len(tags) < self.min_tags:
                self.stdout.write(
                    self.style.WARNING(
                        f"    Only generated {len(tags)} tags (min: {self.min_tags})"
                    )
                )

            return tags

        except Exception as e:
            raise Exception(f"AI tag generation failed: {str(e)}")

    def _clean_tag(self, tag: str) -> str:
        """Clean and normalize a tag name"""
        # Remove any leading/trailing whitespace
        tag = tag.strip()

        # Remove common prefixes that might come from AI
        for prefix in ["tag:", "tags:", "#"]:
            if tag.startswith(prefix):
                tag = tag[len(prefix) :].strip()

        # Ensure lowercase and properly formatted
        tag = tag.lower()

        return tag

    def _apply_tags(self, content_obj, tag_names: List[str]):
        """
        Apply tags to content object, creating tags if they don't exist.

        Args:
            content_obj: Django model instance (Entry, Blogmark, or TIL)
            tag_names: List of tag names to apply
        """
        with transaction.atomic():
            # Clear existing tags if force is enabled
            if self.force:
                content_obj.tags.clear()

            # Get or create each tag and add it
            for tag_name in tag_names:
                tag_slug = slugify(tag_name)
                tag, created = EnhancedTag.objects.get_or_create(
                    slug=tag_slug, defaults={"name": tag_name, "is_active": True}
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"      Created new tag: {tag_name}")
                    )

                content_obj.tags.add(tag)

            content_obj.save()
