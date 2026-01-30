# Scripts Directory

**Consolidated operational scripts for the Minimal Wave Blog project.**

## Overview

This directory contains 5 essential scripts (down from 16) that handle all deployment, migration, and operational tasks.

**Consolidated Scripts** (Use these):
- `migration-safety.sh` - All migration operations
- `azure-ops.sh` - All Azure operations
- `setup-dev-environment.sh` - Developer environment setup
- `scheduled-publishing.sh` - Scheduled content publishing
- `test_azure_storage.py` - Azure storage diagnostics (unchanged)

**Deprecated Scripts** (Will be archived):
- See `.archive/scripts/` directory for old scripts (kept for 30-day reference period)

---

## Quick Reference

### Migration Safety

**Script:** `migration-safety.sh`

```bash
# Pre-flight checklist BEFORE making model changes
./scripts/migration-safety.sh --pre-check

# Validate existing migrations
./scripts/migration-safety.sh --validate

# Test migrations in clean environment (like CI/CD)
./scripts/migration-safety.sh --test-clean

# Check for pending migrations
./scripts/migration-safety.sh --check-pending

# Run all safety checks (validation + clean test)
./scripts/migration-safety.sh --all
```

**What it does:**
- Validates migration dependencies
- Checks for migration conflicts
- Tests migrations in clean environment (backs up/restores DB)
- Shows pre-flight checklist before model changes
- Detects pending uncommitted migrations

**Consolidates:**
- `validate-migrations.sh`
- `validate-migration-dependencies.sh`
- `test-migrations-clean.sh`
- `check-migrations.sh`
- `pre-migration-check.sh` (partial)

---

### Azure Operations

**Script:** `azure-ops.sh`

```bash
# Fix Azure Blob Storage configuration
./scripts/azure-ops.sh --fix-storage

# Diagnose production issues (download logs)
./scripts/azure-ops.sh --diagnose

# Fix Site domain configuration
./scripts/azure-ops.sh --fix-domain

# Run comprehensive health check
./scripts/azure-ops.sh --health-check
```

**What it does:**
- Fixes Azure storage environment variables
- Downloads and analyzes production logs (saves to `.claude-sandbox/`)
- Updates Site domain in Django admin
- Checks App Service status and site availability

**Consolidates:**
- `fix-azure-storage.sh`
- `diagnose_production.sh`
- `fix-site-domain-remote.sh`

---

### Developer Environment Setup

**Script:** `setup-dev-environment.sh`

```bash
# Complete one-time developer environment setup
./scripts/setup-dev-environment.sh
```

**What it does:**
- Sets up shell aliases for safe commands (safe-migrate, validate-mig)
- Installs pre-commit hooks
- Makes all scripts executable
- Verifies Docker installation
- Provides summary of next steps

**Consolidates:**
- `setup-dev-aliases.sh`
- `enforce-dev-environment.sh`
- `docker-usage-warning.sh`

---

### Scheduled Publishing

**Script:** `scheduled-publishing.sh`

```bash
# Set up cron job for hourly publishing
./scripts/scheduled-publishing.sh --setup

# Create test scheduled content
./scripts/scheduled-publishing.sh --test

# Run publishing command now
./scripts/scheduled-publishing.sh --run
```

**What it does:**
- Configures cron job to run `publish_scheduled` hourly
- Creates test Entry and TIL scheduled for 1 hour in future
- Manually triggers publishing of scheduled content

**Consolidates:**
- `setup_scheduled_publishing.sh`
- `test_scheduling.sh`

---

### Azure Storage Diagnostics

**Script:** `test_azure_storage.py`

```bash
# Test Azure storage connectivity and configuration
python scripts/test_azure_storage.py
```

**What it does:**
- Verifies Azure storage credentials
- Tests blob upload/download/delete operations
- Shows storage account configuration
- Identifies connection issues

**Status:** Kept as-is (unique diagnostic functionality)

---

## Make Commands

All scripts have corresponding Make commands for convenience:

### Migration Safety
```bash
make migration-pre-check       # Pre-flight checklist
make makemigrations            # Create migrations with validation
make migrate-safe              # Apply migrations with safety checks
make validate-migrations       # Validate existing migrations
make test-migrations-clean     # Test in clean environment
make check-pending-migrations  # Check for pending migrations
```

### Azure Operations
```bash
make azure-diagnose       # Diagnose production issues
make azure-fix-storage    # Fix storage configuration
make azure-fix-domain     # Fix domain configuration
make azure-health-check   # Comprehensive health check
```

### Scheduled Publishing
```bash
make scheduled-publish-setup   # Set up cron job
make scheduled-publish-test    # Create test content
make publish                   # Publish scheduled content
```

### Developer Setup
```bash
make setup-dev-workflow   # Complete dev environment setup
make setup-pre-commit     # Set up pre-commit hooks
```

---

## Common Workflows

### Starting Development

```bash
# First time setup (run once)
make setup-dev-workflow

# Start development environment
make dev-safe

# Create superuser
make superuser
```

---

### Working with Migrations

```bash
# 1. BEFORE modifying models
make migration-pre-check

# 2. Modify your models in code

# 3. Create migrations
make makemigrations

# 4. Apply migrations safely
make migrate-safe

# 5. Commit changes
git add */migrations/*.py
git commit -m "feat: Add <change> migrations"
```

---

### Troubleshooting Production

```bash
# Run health check
make azure-health-check

# If issues detected, diagnose
make azure-diagnose

# Check logs in .claude-sandbox/prod_diagnosis/

# If storage issues
make azure-fix-storage

# If domain issues
make azure-fix-domain
```

---

### Testing Before Push

```bash
# Validate migrations
make validate-migrations

# Test in CI-like environment
make test-migrations-clean

# Run tests
make test

# All passed? Safe to push!
git push origin main
```

---

## Related Documentation

- **CI/CD Pipeline:** `docs/CI-CD-PIPELINE.md`
- **Development Guide:** `CLAUDE.md`
- **Azure Deployment:** `docs/azure-deployment.md`
- **Azure Storage:** `docs/AZURE_STORAGE_TROUBLESHOOTING.md`

---

## Migration from Old Scripts

**Old script → New command:**

| Old Script | New Command |
|------------|-------------|
| `validate-migrations.sh` | `make validate-migrations` |
| `test-migrations-clean.sh` | `make test-migrations-clean` |
| `check-migrations.sh` | `make check-pending-migrations` |
| `pre-migration-check.sh` | `make migration-pre-check` |
| `fix-azure-storage.sh` | `make azure-fix-storage` |
| `diagnose_production.sh` | `make azure-diagnose` |
| `setup-dev-aliases.sh` | `make setup-dev-workflow` |
| `setup_scheduled_publishing.sh` | `make scheduled-publish-setup` |
