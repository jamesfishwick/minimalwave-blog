# Task Completion Checklist

## Before Committing Code

### 1. Code Quality
```bash
make format              # Format code and templates
```

Expected results:
- Black formatting applied to Python files
- isort applied to imports
- Django templates formatted

### 2. Migration Safety (if models changed)
```bash
make validate-migrations # Check migration integrity
make test-migrations-clean # Test in clean environment
```

Expected results:
- No empty/fake migrations
- No dependency conflicts
- Clean environment tests pass

### 3. Run Tests
```bash
make test               # Run full test suite
```

Expected results:
- All tests pass
- No new test failures introduced

### 4. Pre-commit Hooks
Pre-commit hooks run automatically on commit:
- Trailing whitespace removal
- End-of-file fixing
- Black formatting check
- isort check
- Flake8 linting
- Migration validation
- Django system check
- Security checks (bandit)

Setup once:
```bash
make setup-dev-workflow  # Complete setup with safety
```

## Migration Safety Workflow

### Creating Migrations
```bash
# ALWAYS check current state first
python manage.py showmigrations

# Only create if needed
make makemigrations     # Creates with validation
```

### Applying Migrations
```bash
make migrate-safe       # Applies with safety checks
```

### What Gets Validated
- Empty operations detection
- Dependency graph integrity
- Clean environment compatibility
- CI/CD simulation testing

## Git Workflow
1. Check status: `git status && git branch`
2. Create feature branch: `git checkout -b feature/name`
3. Make changes and test
4. Format code: `make format`
5. Validate: `make validate-migrations` (if needed)
6. Run tests: `make test`
7. Commit: `git commit -m "type(scope): message"`
8. Pre-commit hooks validate automatically
9. Push: `git push`

## Commit Message Format
```
type(scope): subject

- type: feat, fix, docs, style, refactor, test, chore
- scope: blog, til, core, deploy, etc.
- subject: clear description
```

Examples:
- `feat(blog): add scheduled publishing support`
- `fix(til): correct reading time calculation`
- `docs(readme): update deployment instructions`