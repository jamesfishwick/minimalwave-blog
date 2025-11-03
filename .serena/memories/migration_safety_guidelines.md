# Migration Safety Guidelines

## Critical Principles

### 1. Check Before Creating
```bash
# ALWAYS check current state first
python manage.py showmigrations

# Check git status for existing migration files
git status
```

**Never blindly run makemigrations** - assess if migrations are actually needed.

### 2. Safety Workflow (Automated)

#### Setup Once
```bash
make setup-dev-workflow    # Complete safety setup
make setup-pre-commit      # Pre-commit hooks only
```

#### Daily Usage
```bash
make makemigrations        # Creates with validation
make migrate-safe          # Applies with safety checks
```

### 3. What the Safety System Prevents
- Empty/fake migrations (no actual database operations)
- Migration dependency conflicts
- Migrations that work locally but fail in CI/CD
- Inconsistent database state between environments

## Manual Safety Checks

### Before Creating Migrations
1. Check existing migrations: `python manage.py showmigrations`
2. Check git status: `git status` (look for migration files)
3. Verify models actually changed
4. Only run `makemigrations` if genuinely needed

### After Creating Migrations
1. Review migration file content
2. Validate: `make validate-migrations`
3. Test in clean environment: `make test-migrations-clean`
4. Commit migration files with related model changes

## How Safety System Works

### Pre-commit Hooks
Automatically run before each commit:
1. `check-migrations.sh` - Detects pending migrations
2. `validate-migrations.sh` - Checks migration integrity
3. `validate-migration-dependencies.sh` - Verifies dependency graph

### Pre-push Hooks
Run before pushing to remote:
1. `test-migrations-clean.sh` - Full clean environment test

### Migration Validation
- Scans migration files for empty operations
- Checks dependency graph for conflicts
- Tests in isolated environment (simulates CI/CD)
- Validates cross-environment compatibility

## Common Issues Prevented

### Empty Migrations
**Problem**: Migration files created with no actual operations
**Detection**: validate-migrations.sh scans for empty operations lists
**Prevention**: Automated validation catches before commit

### Dependency Conflicts
**Problem**: Circular or broken migration dependencies
**Detection**: Dependency graph analysis
**Prevention**: Pre-commit validation fails if conflicts detected

### CI/CD Failures
**Problem**: Migrations work locally but fail in fresh environments
**Detection**: Clean environment testing simulates CI/CD
**Prevention**: test-migrations-clean.sh catches environment-specific issues

## Emergency Procedures

### If Validation Fails
1. Review the validation error message
2. Check migration file content
3. Fix the issue (delete/recreate migration if needed)
4. Re-run validation: `make validate-migrations`

### If Clean Environment Test Fails
1. Review test output for specific errors
2. Check database state consistency
3. May need to reset migrations or database
4. Seek help if encountering repeatedly

## Best Practices
- **Run code in Docker** - Ensures environment consistency
- **Use safety commands** - `make makemigrations`, `make migrate-safe`
- **Validate before commit** - `make validate-migrations`
- **Test before push** - `make test-migrations-clean`
- **Never skip validation** - Safety checks exist to prevent production issues