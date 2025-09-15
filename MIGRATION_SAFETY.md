# Migration Safety Guide

## Root Causes & Solutions

**What went wrong:**
- Used `docker-compose.yml` (no source mounting) vs dev environment → files didn't sync
- Created duplicate/conflicting migrations without checking state
- Field constraint issues without proper defaults

**Prevention system implemented:**
- Environment enforcement (proper Docker setup)
- Pre-migration validation & dependency checking
- Automated pre-commit hooks
- Safe workflow commands

## Quick Reference

### Development Setup
```bash
make dev                    # Start with source mounting (REQUIRED)
make setup-pre-commit       # Install validation hooks
```

### Safe Migration Workflow
```bash
# 1. Check state before changes
./scripts/pre-migration-check.sh

# 2. Make model changes, then:
make makemigrations         # Safe creation with validation

# 3. Validate before committing
make test-migrations-clean

# 4. Commit (hooks auto-validate)
git add models.py migrations/*.py
git commit -m "Add field with migration"
```

### Recovery Commands
```bash
python manage.py showmigrations                    # Diagnose
./scripts/validate-migration-dependencies.sh       # Check graph
make test-migrations-clean                         # Test clean
```

## Critical Rules

1. **Always use `make dev`** (not `docker-compose up`)
2. **Check state before model changes** (`./scripts/pre-migration-check.sh`)
3. **Atomic commits** (model + migration together)
4. **Never bypass pre-commit hooks**
5. **Provide defaults for non-nullable fields**

## Anti-Patterns

❌ Using basic `docker-compose` commands  
❌ Making model changes without state checking  
❌ Manually editing migration dependencies  
❌ Committing models without migrations  
❌ Skipping validation steps  

## Automated Protection

**Pre-commit hooks validate:**
- Migration dependency graph integrity
- Duplicate field detection
- Clean environment compatibility

**Make commands enforce:**
- Development environment with source mounting
- Validation before migration creation
- Clean environment testing

## Prevention Coverage

✅ Docker sync issues (environment enforcement)  
✅ Dependency conflicts (graph validation)  
✅ Duplicate fields (automated detection)  
✅ CI/CD failures (clean testing)  
✅ Field constraints (state checking)  

**This system prevents the migration issues we experienced from happening again.**