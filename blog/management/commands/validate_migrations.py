"""
Management command to validate migration consistency.
This prevents deployment of migrations that would cause dependency issues.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.apps import apps
import sys


class Command(BaseCommand):
    help = 'Validate migration consistency and dependencies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Exit with error code if any issues found',
        )

    def handle(self, *args, **options):
        errors = []
        warnings = []

        # Load the migration loader
        loader = MigrationLoader(connection)

        self.stdout.write("=== Migration Validation Report ===\n")

        # Check 1: Verify all migration dependencies exist
        self.stdout.write("1. Checking migration dependencies...")
        for (app_label, migration_name), migration in loader.disk_migrations.items():
            for dep_app, dep_migration in migration.dependencies:
                if dep_app == '__first__':
                    continue

                dep_key = (dep_app, dep_migration)
                if dep_key not in loader.disk_migrations:
                    error = f"Migration {app_label}.{migration_name} depends on {dep_app}.{dep_migration} which doesn't exist"
                    errors.append(error)
                    self.stdout.write(f"   ❌ {error}")

        if not errors:
            self.stdout.write("   ✅ All migration dependencies exist")

        # Check 2: Look for circular dependencies
        self.stdout.write("\n2. Checking for circular dependencies...")
        circular_deps = self._find_circular_dependencies(loader)
        if circular_deps:
            for cycle in circular_deps:
                error = f"Circular dependency detected: {' -> '.join(cycle)}"
                errors.append(error)
                self.stdout.write(f"   ❌ {error}")
        else:
            self.stdout.write("   ✅ No circular dependencies found")

        # Check 3: Validate that initial migrations don't depend on later ones
        self.stdout.write("\n3. Checking initial migration dependencies...")
        for (app_label, migration_name), migration in loader.disk_migrations.items():
            if migration_name == '0001_initial':
                for dep_app, dep_migration in migration.dependencies:
                    if dep_app != '__first__' and dep_app != 'auth' and dep_app != 'contenttypes':
                        # Check if the dependency app has migrations that might not exist in production
                        if dep_app in [app.label for app in apps.get_app_configs()]:
                            warning = f"Initial migration {app_label}.{migration_name} depends on {dep_app}.{dep_migration} - this could cause production issues"
                            warnings.append(warning)
                            self.stdout.write(f"   ⚠️  {warning}")

        if not warnings:
            self.stdout.write("   ✅ Initial migration dependencies look safe")

        # Check 4: Verify no empty migrations (they often indicate problems)
        self.stdout.write("\n4. Checking for empty migrations...")
        empty_migrations = []
        for (app_label, migration_name), migration in loader.disk_migrations.items():
            if not migration.operations:
                empty_migrations.append(f"{app_label}.{migration_name}")

        if empty_migrations:
            for empty_mig in empty_migrations:
                warning = f"Empty migration detected: {empty_mig}"
                warnings.append(warning)
                self.stdout.write(f"   ⚠️  {warning}")
        else:
            self.stdout.write("   ✅ No empty migrations found")

        # Check 5: Look for recently regenerated initial migrations
        self.stdout.write("\n5. Checking for regenerated initial migrations...")
        regenerated = self._check_regenerated_initials(loader)
        if regenerated:
            for regen in regenerated:
                warning = f"Initial migration may have been regenerated: {regen}"
                warnings.append(warning)
                self.stdout.write(f"   ⚠️  {warning}")
        else:
            self.stdout.write("   ✅ No regenerated initial migrations detected")

        # Summary
        self.stdout.write(f"\n=== Summary ===")
        self.stdout.write(f"Errors: {len(errors)}")
        self.stdout.write(f"Warnings: {len(warnings)}")

        if errors:
            self.stdout.write(f"\n❌ Migration validation FAILED with {len(errors)} errors")
            for error in errors:
                self.stdout.write(f"   • {error}")

        if warnings:
            self.stdout.write(f"\n⚠️  Found {len(warnings)} warnings")
            for warning in warnings:
                self.stdout.write(f"   • {warning}")

        if not errors and not warnings:
            self.stdout.write("\n✅ All migration validations passed")

        # Exit with error code if strict mode and issues found
        if options['strict'] and (errors or warnings):
            sys.exit(1)
        elif errors:
            sys.exit(1)

    def _find_circular_dependencies(self, loader):
        """Detect circular dependencies in migrations"""
        circular = []
        visited = set()
        path = []

        def visit(node):
            if node in path:
                cycle_start = path.index(node)
                circular.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            if node in loader.disk_migrations:
                migration = loader.disk_migrations[node]
                for dep_app, dep_name in migration.dependencies:
                    if dep_app != '__first__':
                        dep_node = (dep_app, dep_name)
                        visit(dep_node)

            path.pop()

        for node in loader.disk_migrations:
            if node not in visited:
                visit(node)

        return circular

    def _check_regenerated_initials(self, loader):
        """Check for signs that initial migrations were regenerated"""
        regenerated = []

        for (app_label, migration_name), migration in loader.disk_migrations.items():
            if migration_name == '0001_initial':
                # Check if it has dependencies on other apps' initial migrations
                # This is a common sign of regeneration
                non_standard_deps = []
                for dep_app, dep_name in migration.dependencies:
                    if dep_app not in ['__first__', 'auth', 'contenttypes', 'sessions', 'sites']:
                        if dep_name == '0001_initial':
                            non_standard_deps.append(f"{dep_app}.{dep_name}")

                if non_standard_deps:
                    regenerated.append(f"{app_label}.{migration_name} -> depends on {non_standard_deps}")

        return regenerated