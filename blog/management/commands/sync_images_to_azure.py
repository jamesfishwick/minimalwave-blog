"""
Django management command to sync images to Azure Blob Storage.

This command is useful when:
1. Migrating from local storage to Azure Blob Storage
2. Re-uploading images that failed to upload
3. Fixing broken image references

Usage:
    python manage.py sync_images_to_azure [--dry-run] [--force]
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from blog.models import Entry, Blogmark


class Command(BaseCommand):
    help = 'Sync images to Azure Blob Storage and report missing files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-upload of all images',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Check Azure storage configuration
        if not hasattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME'):
            self.stdout.write(
                self.style.ERROR('❌ Azure Storage not configured!')
            )
            self.stdout.write(
                'Set AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY environment variables'
            )
            return

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Image Sync to Azure Blob Storage'))
        self.stdout.write('='*70 + '\n')

        # Check Entry images
        self.stdout.write(self.style.HTTP_INFO('📝 Checking blog entries...'))
        self.check_entries(Entry.objects.all(), dry_run, force)

        # Check Blogmark images
        self.stdout.write(self.style.HTTP_INFO('\n🔗 Checking blogmarks...'))
        self.check_entries(Blogmark.objects.all(), dry_run, force)

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ Sync complete!'))
        self.stdout.write('='*70 + '\n')

    def check_entries(self, queryset, dry_run, force):
        """Check entries for image issues"""
        entries_with_images = queryset.exclude(image='')
        total = entries_with_images.count()

        if total == 0:
            self.stdout.write('  No entries with images found.')
            return

        self.stdout.write(f'  Found {total} entries with images\n')

        missing_count = 0
        existing_count = 0

        for entry in entries_with_images:
            status = self.check_image(entry, dry_run, force)
            if status == 'missing':
                missing_count += 1
            elif status == 'exists':
                existing_count += 1

        # Summary
        self.stdout.write(f'\n  Summary:')
        self.stdout.write(f'    ✅ Existing: {existing_count}')
        if missing_count > 0:
            self.stdout.write(
                self.style.ERROR(f'    ❌ Missing: {missing_count}')
            )
            self.stdout.write(
                self.style.WARNING(
                    '\n    ⚠️  Missing images need to be re-uploaded through Django admin'
                )
            )

    def check_image(self, entry, dry_run, force):
        """Check if an image exists"""
        if not entry.image:
            return None

        try:
            # Try to access the file
            if entry.image.storage.exists(entry.image.name):
                self.stdout.write(
                    f'    ✅ {entry.title[:50]}: {entry.image.name}'
                )
                return 'exists'
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'    ❌ {entry.title[:50]}: MISSING - {entry.image.name}'
                    )
                )
                self.stdout.write(
                    f'       Entry ID: {entry.id}'
                )
                self.stdout.write(
                    f'       Admin URL: /admin/blog/entry/{entry.id}/change/'
                )
                return 'missing'
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'    ⚠️  {entry.title[:50]}: ERROR - {str(e)}'
                )
            )
            return 'error'
