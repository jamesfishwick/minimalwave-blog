# Migration Safety Workflow

This document outlines the **mandatory process** for making model changes to prevent migration issues.

## ⚠️ CRITICAL: Follow This Process Exactly

**Never skip steps or make shortcuts. The recent migration issues were caused by not following this process.**

## 1. Pre-Change Assessment

```bash
# ALWAYS run this first
./scripts/pre-migration-check.sh

# Check current migration state
python manage.py showmigrations

# Verify no pending migrations
python manage.py makemigrations --check --dry-run
```

**If pending migrations exist: STOP and commit them first before making new changes.**

## 2. Model Changes

Make your model changes in `models.py` files.

**Rules:**

- Make atomic changes (one logical change per commit)
- For field constraint changes (nullable to non-nullable), always provide defaults
- Never remove fields without a deprecation migration first

## 3. Migration Creation

```bash
# Create migrations using the safe workflow
make makemigrations

# This runs:
# 1. python manage.py makemigrations
# 2. Automatic validation
# 3. Dependency checking
```

**Never manually edit migration files unless absolutely necessary.**

## 4. Migration Validation

```bash
# Validate migration dependencies
./scripts/validate-migration-dependencies.sh

# Test in clean environment
make test-migrations-clean
```

## 5. Container/Local Sync Verification

**Critical: Ensure Docker container changes are synced to local files**

```bash
# Check that migration files exist locally
ls -la */migrations/

# If migrations were created in container, copy them:
docker cp container_name:/app/app_name/migrations/XXXX_migration.py app_name/migrations/
```

## 6. Commit Process

```bash
# Stage model changes AND migration files together
git add app_name/models.py app_name/migrations/XXXX_*.py

# Atomic commit
git commit -m "Add field_name to Model

- Add field with proper constraints
- Include migration for database schema update
- Field allows null/blank for backward compatibility"
```

## 7. Pre-Push Validation

The pre-commit hooks will automatically run:

- Migration dependency validation
- Clean environment testing (on push)
- Django system checks

**Do not bypass pre-commit hooks with --no-verify**

## Common Anti-Patterns to Avoid

❌ **Making model changes without checking existing migrations**
❌ **Creating migrations in Docker without syncing to local files**
❌ **Manually editing migration dependencies**
❌ **Committing model changes without corresponding migrations**
❌ **Adding non-nullable fields without defaults**
❌ **Skipping pre-commit validation**

## Emergency Recovery

If you encounter migration issues:

```bash
# 1. Check what's wrong
python manage.py showmigrations
python manage.py makemigrations --check --dry-run

# 2. Fix dependency issues
./scripts/validate-migration-dependencies.sh

# 3. Test clean migration path
make test-migrations-clean

# 4. If needed, squash migrations
python manage.py squashmigrations app_name start_migration end_migration
```

## Development Environment Setup

```bash
# Set up the complete migration safety system
make setup-pre-commit

# This installs:
# - Pre-commit hooks
# - Migration validation scripts
# - Clean environment testing
```

## Makefile Commands Reference

```bash
make makemigrations        # Safe migration creation with validation
make migrate-safe          # Apply migrations with testing
make validate-migrations   # Check existing migrations
make test-migrations-clean # Test in CI-like environment
make setup-pre-commit      # Install complete safety system
```

**Remember: The recent issues were caused by not following this workflow. Always follow every step.**
