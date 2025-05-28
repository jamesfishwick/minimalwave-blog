"""
Management command to publish scheduled content that is due.
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from blog.models import Entry, Blogmark

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Publish scheduled blog content whose publish_date has passed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would be published without actually publishing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        if dry_run:
            self.stdout.write("DRY RUN: Checking for content to publish...")
        else:
            self.stdout.write("Publishing scheduled content...")

        # Find entries with publish dates that have passed but are still marked as draft/review
        entries_to_publish = Entry.objects.filter(
            ~Q(status='published'),
            publish_date__lte=now
        )

        # Find blogmarks with publish dates that have passed but are still marked as draft/review
        blogmarks_to_publish = Blogmark.objects.filter(
            ~Q(status='published'),
            publish_date__lte=now
        )

        # Process entries
        count_entries = 0
        for entry in entries_to_publish:
            if dry_run:
                self.stdout.write(f"Would publish entry: {entry.title} (scheduled for {entry.publish_date})")
            else:
                entry.status = 'published'
                entry.is_draft = False
                entry.save()
                count_entries += 1
                self.stdout.write(f"Published entry: {entry.title}")

        # Process blogmarks
        count_blogmarks = 0
        for blogmark in blogmarks_to_publish:
            if dry_run:
                self.stdout.write(f"Would publish blogmark: {blogmark.title} (scheduled for {blogmark.publish_date})")
            else:
                blogmark.status = 'published'
                blogmark.is_draft = False
                blogmark.save()
                count_blogmarks += 1
                self.stdout.write(f"Published blogmark: {blogmark.title}")

        # Output summary
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"DRY RUN COMPLETE: Found {len(entries_to_publish)} entries and {len(blogmarks_to_publish)} blogmarks ready to publish"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Published {count_entries} entries and {count_blogmarks} blogmarks"
            ))
