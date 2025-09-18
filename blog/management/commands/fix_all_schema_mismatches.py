"""
Comprehensive management command to fix all schema mismatches between models and database.
This handles all the column and table issues that arose from the model restructuring.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
import sys


class Command(BaseCommand):
    help = 'Fix all schema mismatches between Django models and database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Comprehensive Schema Fix ===\n")

        with connection.cursor() as cursor:
            fixes_applied = []

            # Check core_enhancedtag table structure
            self.stdout.write("1. Checking core_enhancedtag table...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'core_enhancedtag'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()

            if not columns:
                self.stdout.write("   ❌ core_enhancedtag table does not exist")
                return

            existing_columns = {col[0]: (col[1], col[2]) for col in columns}
            self.stdout.write("   Current columns:")
            for col_name, (col_type, nullable) in existing_columns.items():
                null_str = "NULL" if nullable == "YES" else "NOT NULL"
                self.stdout.write(f"     - {col_name} ({col_type}, {null_str})")

            # Define expected columns for core_enhancedtag based on the model
            expected_columns = {
                'id': ('serial', 'NOT NULL'),
                'name': ('character varying(50)', 'NOT NULL'),
                'slug': ('character varying(50)', 'NOT NULL'),
                'description': ('text', 'NOT NULL'),
                'category_id': ('bigint', 'NULL'),
                'content_type': ('character varying(10)', 'NOT NULL'),
                'color': ('character varying(7)', 'NOT NULL'),
                'icon': ('character varying(50)', 'NOT NULL'),
                'usage_count': ('integer', 'NOT NULL'),
                'last_used': ('timestamp with time zone', 'NULL'),
                'is_featured': ('boolean', 'NOT NULL'),
                'is_active': ('boolean', 'NOT NULL'),
                'created': ('timestamp with time zone', 'NOT NULL'),
                'updated': ('timestamp with time zone', 'NOT NULL'),
            }

            # Check for missing columns
            missing_columns = []
            for col_name, (expected_type, expected_null) in expected_columns.items():
                if col_name not in existing_columns:
                    missing_columns.append((col_name, expected_type, expected_null))

            if missing_columns:
                self.stdout.write(f"   🔍 Found {len(missing_columns)} missing columns:")
                for col_name, col_type, nullable in missing_columns:
                    self.stdout.write(f"     - {col_name} ({col_type}, {nullable})")

                if not options['dry_run']:
                    self.stdout.write("   🔧 Adding missing columns...")
                    with transaction.atomic():
                        for col_name, col_type, nullable in missing_columns:
                            default_value = self._get_default_value(col_name, col_type, nullable)
                            null_constraint = "" if nullable == "NULL" else " NOT NULL"

                            sql = f"ALTER TABLE core_enhancedtag ADD COLUMN {col_name} {col_type}{null_constraint}"
                            if default_value:
                                sql += f" DEFAULT {default_value}"

                            try:
                                cursor.execute(sql)
                                self.stdout.write(f"     ✅ Added {col_name}")
                                fixes_applied.append(f"Added column core_enhancedtag.{col_name}")
                            except Exception as e:
                                self.stdout.write(f"     ❌ Error adding {col_name}: {e}")

            # Also fix TIL table if needed
            self.stdout.write("\n2. Checking til_til table...")
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'til_til'
                )
            """)
            til_exists = cursor.fetchone()[0]

            if til_exists:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = 'til_til'
                    AND column_name = 'enhancedtag_id'
                """)
                has_enhancedtag_id = cursor.fetchone()

                if not has_enhancedtag_id:
                    # Check if it has tag_id instead
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = 'til_til_tags'
                        AND column_name = 'tag_id'
                    """)
                    has_tag_id = cursor.fetchone()

                    if has_tag_id and not options['dry_run']:
                        self.stdout.write("   🔧 Fixing TIL tags table...")
                        try:
                            # Drop foreign key constraint
                            cursor.execute("ALTER TABLE til_til_tags DROP CONSTRAINT IF EXISTS til_til_tags_tag_id_fkey")

                            # Rename column
                            cursor.execute("ALTER TABLE til_til_tags RENAME COLUMN tag_id TO enhancedtag_id")

                            # Recreate foreign key
                            cursor.execute("""
                                ALTER TABLE til_til_tags
                                ADD CONSTRAINT til_til_tags_enhancedtag_id_fkey
                                FOREIGN KEY (enhancedtag_id) REFERENCES core_enhancedtag(id)
                                DEFERRABLE INITIALLY DEFERRED
                            """)

                            self.stdout.write("   ✅ Fixed TIL tags table")
                            fixes_applied.append("Fixed til_til_tags.tag_id -> enhancedtag_id")

                        except Exception as e:
                            self.stdout.write(f"   ❌ Error fixing TIL tags: {e}")

            # Summary
            if fixes_applied:
                self.stdout.write(f"\n✅ Applied {len(fixes_applied)} fixes:")
                for fix in fixes_applied:
                    self.stdout.write(f"   - {fix}")
            else:
                self.stdout.write("\n✅ No schema fixes needed")

    def _get_default_value(self, col_name, col_type, nullable):
        """Get appropriate default value for a column"""
        defaults = {
            'content_type': "'all'",
            'color': "''",
            'icon': "''",
            'usage_count': '0',
            'is_featured': 'false',
            'is_active': 'true',
            'created': 'NOW()',
            'updated': 'NOW()',
            'description': "''",
        }
        return defaults.get(col_name, None)