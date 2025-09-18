"""
Management command to fix schema alignment issues between models and database.
This fixes column naming mismatches that can occur after migration restructuring.
"""

from django.core.management.base import BaseCommand
from django.db import connection
import sys


class Command(BaseCommand):
    help = 'Fix schema alignment issues between Django models and database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Schema Alignment Check ===\n")

        with connection.cursor() as cursor:

            # Check blog_entry_tags table structure
            self.stdout.write("1. Checking blog_entry_tags table...")
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'blog_entry_tags'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()

            if not columns:
                self.stdout.write("   ❌ blog_entry_tags table does not exist")
                sys.exit(1)

            self.stdout.write("   Current columns:")
            for col_name, col_type in columns:
                self.stdout.write(f"     - {col_name} ({col_type})")

            # Check what Django expects
            expected_columns = ['id', 'entry_id', 'enhancedtag_id']
            actual_columns = [col[0] for col in columns]

            self.stdout.write(f"   Expected: {expected_columns}")
            self.stdout.write(f"   Actual: {actual_columns}")

            # Look for misnamed columns
            fixes_needed = []

            # Common mapping issues
            if 'tag_id' in actual_columns and 'enhancedtag_id' not in actual_columns:
                fixes_needed.append(('tag_id', 'enhancedtag_id'))
                self.stdout.write("   🔍 Found: tag_id should be enhancedtag_id")

            # Check blogmark_tags table too
            self.stdout.write("\n2. Checking blog_blogmark_tags table...")
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'blog_blogmark_tags'
                ORDER BY ordinal_position
            """)
            blogmark_columns = cursor.fetchall()

            if blogmark_columns:
                self.stdout.write("   Current columns:")
                for col_name, col_type in blogmark_columns:
                    self.stdout.write(f"     - {col_name} ({col_type})")

                actual_blogmark_columns = [col[0] for col in blogmark_columns]
                if 'tag_id' in actual_blogmark_columns and 'enhancedtag_id' not in actual_blogmark_columns:
                    fixes_needed.append(('blog_blogmark_tags', 'tag_id', 'enhancedtag_id'))
                    self.stdout.write("   🔍 Found: tag_id should be enhancedtag_id in blogmark_tags")

            # Check constraints that might need updating
            self.stdout.write("\n3. Checking foreign key constraints...")
            cursor.execute("""
                SELECT tc.constraint_name, tc.table_name, kcu.column_name,
                       ccu.table_name AS foreign_table_name,
                       ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('blog_entry_tags', 'blog_blogmark_tags')
            """)
            constraints = cursor.fetchall()

            for constraint in constraints:
                self.stdout.write(f"   - {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]}")

            # Apply fixes
            if fixes_needed:
                self.stdout.write(f"\n=== Fixes Needed: {len(fixes_needed)} ===")

                for fix in fixes_needed:
                    if len(fix) == 2:  # Entry tags fix
                        old_col, new_col = fix
                        table = 'blog_entry_tags'
                    else:  # Blogmark tags fix
                        table, old_col, new_col = fix

                    self.stdout.write(f"Renaming {table}.{old_col} to {new_col}")

                    if not options['dry_run']:
                        try:
                            # Drop foreign key constraint first
                            cursor.execute(f"""
                                ALTER TABLE {table}
                                DROP CONSTRAINT IF EXISTS {table}_{old_col}_fkey
                            """)

                            # Rename the column
                            cursor.execute(f"""
                                ALTER TABLE {table}
                                RENAME COLUMN {old_col} TO {new_col}
                            """)

                            # Recreate foreign key constraint with new name
                            cursor.execute(f"""
                                ALTER TABLE {table}
                                ADD CONSTRAINT {table}_{new_col}_fkey
                                FOREIGN KEY ({new_col}) REFERENCES core_enhancedtag(id)
                                DEFERRABLE INITIALLY DEFERRED
                            """)

                            self.stdout.write(f"   ✅ Renamed {table}.{old_col} to {new_col}")

                        except Exception as e:
                            self.stdout.write(f"   ❌ Error renaming {table}.{old_col}: {e}")

                    else:
                        self.stdout.write(f"   🔍 Would rename {table}.{old_col} to {new_col}")

                if not options['dry_run']:
                    self.stdout.write("\n✅ Schema alignment completed")
                else:
                    self.stdout.write("\n🔍 Dry run completed - use --dry-run=false to apply changes")
            else:
                self.stdout.write("\n✅ No schema alignment issues found")