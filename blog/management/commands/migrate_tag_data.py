"""
Management command to migrate tag data from old blog_tag table to new core_enhancedtag table.
This handles the data migration that was missed during the model restructuring.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
import sys


class Command(BaseCommand):
    help = 'Migrate tag data from blog_tag to core_enhancedtag and update references'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Tag Data Migration ===\n")

        with connection.cursor() as cursor:

            # Check if old blog_tag table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'blog_tag'
                )
            """)
            blog_tag_exists = cursor.fetchone()[0]

            if not blog_tag_exists:
                self.stdout.write("✅ blog_tag table doesn't exist - migration may already be complete")
                return

            # Check current data
            cursor.execute("SELECT COUNT(*) FROM blog_tag")
            blog_tag_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM core_enhancedtag")
            core_tag_count = cursor.fetchone()[0]

            self.stdout.write(f"Old blog_tag table: {blog_tag_count} tags")
            self.stdout.write(f"New core_enhancedtag table: {core_tag_count} tags")

            if blog_tag_count == 0:
                self.stdout.write("✅ No tags to migrate from blog_tag")
                return

            # Check for conflicting data
            cursor.execute("""
                SELECT bt.name
                FROM blog_tag bt
                JOIN core_enhancedtag ct ON bt.name = ct.name
            """)
            conflicts = cursor.fetchall()

            if conflicts:
                self.stdout.write(f"⚠️  Found {len(conflicts)} tag names that exist in both tables:")
                for conflict in conflicts[:5]:  # Show first 5
                    self.stdout.write(f"   - {conflict[0]}")
                if len(conflicts) > 5:
                    self.stdout.write(f"   ... and {len(conflicts) - 5} more")

            if not options['dry_run']:
                self.stdout.write("\n🚀 Starting migration...")

                with transaction.atomic():
                    # Create mapping of old blog_tag ids to new core_enhancedtag ids
                    tag_mapping = {}

                    # Migrate tags that don't exist in core_enhancedtag
                    cursor.execute("""
                        SELECT bt.id, bt.name, bt.slug
                        FROM blog_tag bt
                        LEFT JOIN core_enhancedtag ct ON bt.name = ct.name
                        WHERE ct.name IS NULL
                    """)
                    new_tags = cursor.fetchall()

                    for old_id, name, slug in new_tags:
                        # Create new enhanced tag
                        cursor.execute("""
                            INSERT INTO core_enhancedtag (name, slug, content_type, is_active, created, updated)
                            VALUES (%s, %s, 'all', true, NOW(), NOW())
                            RETURNING id
                        """, [name, slug])
                        new_id = cursor.fetchone()[0]
                        tag_mapping[old_id] = new_id
                        self.stdout.write(f"   ✅ Migrated tag '{name}': {old_id} -> {new_id}")

                    # Handle existing tags (map old id to existing new id)
                    cursor.execute("""
                        SELECT bt.id, ct.id
                        FROM blog_tag bt
                        JOIN core_enhancedtag ct ON bt.name = ct.name
                    """)
                    existing_mappings = cursor.fetchall()

                    for old_id, new_id in existing_mappings:
                        tag_mapping[old_id] = new_id
                        self.stdout.write(f"   🔗 Mapped existing tag: {old_id} -> {new_id}")

                    # Update blog_entry_tags references
                    cursor.execute("SELECT COUNT(*) FROM blog_entry_tags WHERE tag_id IS NOT NULL")
                    entry_tag_count = cursor.fetchone()[0]

                    if entry_tag_count > 0:
                        self.stdout.write(f"\n🔄 Updating {entry_tag_count} entry-tag relationships...")

                        for old_id, new_id in tag_mapping.items():
                            cursor.execute("""
                                UPDATE blog_entry_tags
                                SET tag_id = %s
                                WHERE tag_id = %s
                            """, [new_id, old_id])
                            updated = cursor.rowcount
                            if updated > 0:
                                self.stdout.write(f"   ✅ Updated {updated} entry-tag references: {old_id} -> {new_id}")

                    # Update blog_blogmark_tags references (if using old schema)
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_schema = 'public'
                            AND table_name = 'blog_blogmark_tags'
                            AND column_name = 'tag_id'
                        )
                    """)
                    blogmark_has_old_column = cursor.fetchone()[0]

                    if blogmark_has_old_column:
                        cursor.execute("SELECT COUNT(*) FROM blog_blogmark_tags WHERE tag_id IS NOT NULL")
                        blogmark_tag_count = cursor.fetchone()[0]

                        if blogmark_tag_count > 0:
                            self.stdout.write(f"\n🔄 Updating {blogmark_tag_count} blogmark-tag relationships...")

                            for old_id, new_id in tag_mapping.items():
                                cursor.execute("""
                                    UPDATE blog_blogmark_tags
                                    SET tag_id = %s
                                    WHERE tag_id = %s
                                """, [new_id, old_id])
                                updated = cursor.rowcount
                                if updated > 0:
                                    self.stdout.write(f"   ✅ Updated {updated} blogmark-tag references: {old_id} -> {new_id}")

                    self.stdout.write(f"\n✅ Migration completed! Migrated {len(tag_mapping)} tags")

            else:
                self.stdout.write("\n🔍 Dry run mode - would migrate:")
                cursor.execute("""
                    SELECT bt.id, bt.name, bt.slug
                    FROM blog_tag bt
                    LEFT JOIN core_enhancedtag ct ON bt.name = ct.name
                    WHERE ct.name IS NULL
                """)
                new_tags = cursor.fetchall()

                for old_id, name, slug in new_tags:
                    self.stdout.write(f"   Would create: {name} (slug: {slug})")

                cursor.execute("""
                    SELECT bt.id, ct.id, bt.name
                    FROM blog_tag bt
                    JOIN core_enhancedtag ct ON bt.name = ct.name
                """)
                existing_mappings = cursor.fetchall()

                for old_id, new_id, name in existing_mappings:
                    self.stdout.write(f"   Would map: {name} ({old_id} -> {new_id})")