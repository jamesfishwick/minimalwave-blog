# Archive Directory

**Deprecated files kept for reference (30-day retention period)**

## What's Here

This directory contains files that have been consolidated or replaced as part of the deployment strategy consolidation.

**Archived:** 2026-01-30
**Retention:** 30 days (until 2026-03-01)
**Related:** #consolidate-deployment

---

## Archived Scripts (14 files)

### Migration Safety (5 scripts)
- `validate-migrations.sh` → Replaced by `migration-safety.sh --validate`
- `validate-migration-dependencies.sh` → Replaced by `migration-safety.sh --validate`
- `test-migrations-clean.sh` → Replaced by `migration-safety.sh --test-clean`
- `check-migrations.sh` → Replaced by `migration-safety.sh --check-pending`
- `pre-migration-check.sh` → Replaced by `migration-safety.sh --pre-check`

### Azure Operations (3 scripts)
- `fix-azure-storage.sh` → Replaced by `azure-ops.sh --fix-storage`
- `diagnose_production.sh` → Replaced by `azure-ops.sh --diagnose`
- `fix-site-domain-remote.sh` → Replaced by `azure-ops.sh --fix-domain`
- `check_storage_config.py` → Diagnostic functionality merged into azure-ops.sh

### Developer Setup (3 scripts)
- `setup-dev-aliases.sh` → Replaced by `setup-dev-environment.sh`
- `enforce-dev-environment.sh` → Replaced by `setup-dev-environment.sh`
- `docker-usage-warning.sh` → Replaced by `setup-dev-environment.sh`

### Scheduled Publishing (2 scripts)
- `setup_scheduled_publishing.sh` → Replaced by `scheduled-publishing.sh --setup`
- `test_scheduling.sh` → Replaced by `scheduled-publishing.sh --test`

---

## Archived Workflows (2 files)

- `migration-validation.yml` → Replaced by `ci-cd.yml` (Job 1)
- `azure-deploy.yml` → Replaced by `ci-cd.yml` (Job 2)

---

## Migration Guide

### Old Commands → New Commands

**Migration Safety:**
```bash
# Old
./scripts/validate-migrations.sh
# New
make validate-migrations

# Old
./scripts/test-migrations-clean.sh
# New
make test-migrations-clean
```

**Azure Operations:**
```bash
# Old
./scripts/fix-azure-storage.sh
# New
make azure-fix-storage

# Old
./scripts/diagnose_production.sh
# New
make azure-diagnose
```

**Developer Setup:**
```bash
# Old
./scripts/setup-dev-aliases.sh
# New
make setup-dev-workflow
```

**Scheduled Publishing:**
```bash
# Old
./scripts/setup_scheduled_publishing.sh
# New
make scheduled-publish-setup
```

See `scripts/README.md` for complete migration guide.

---

## Why This Change?

**Before:** 16 scripts, 2 workflows
**After:** 5 scripts, 1 workflow

**Benefits:**
- 69% reduction in scripts
- Single unified CI/CD pipeline
- PostgreSQL testing in CI (matches production)
- Easier to maintain
- Single source of truth for deployment

---

## Rollback Instructions

If you need to rollback to old scripts:

```bash
# Copy scripts back
cp .archive/scripts/* scripts/

# Copy workflows back
cp .archive/workflows/* .github/workflows/

# Commit the rollback
git add scripts/ .github/workflows/
git commit -m "Rollback: Restore old scripts and workflows"
git push origin main
```

---

## Deletion Schedule

**Archive created:** 2026-01-30
**Review date:** 2026-02-15 (15 days)
**Deletion date:** 2026-03-01 (30 days)

After 30 days, this directory will be deleted if no issues reported.

---

## Documentation

- **New CI/CD:** `docs/CI-CD-PIPELINE.md`
- **Scripts Guide:** `scripts/README.md`
- **Development Guide:** `CLAUDE.md`
