
---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development (Virtual Environment)

````bash`
# Run development server
python manage.py runserver 0.0.0.0:8000

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Testing
python manage.py test
pytest

# Code formatting
black blog til minimalwave-blog
isort blog til minimalwave-blog
python format_django_templates.py

# Scheduled publishing
python manage.py publish_scheduled
```

### Docker Development

```bash
# Start development environment
docker-compose up -d
make dev

# Production environment
docker-compose -f docker-compose.prod.yml up -d
make prod

# Execute commands in container (prefer Make commands)
make migrate-safe  # Recommended over docker-compose exec web python manage.py migrate
make superuser     # Or: docker-compose exec web python manage.py createsuperuser
```

### Development Admin Access

**Pre-configured Admin Accounts:**
- **Admin User**: `admin` / `adminpass123`
- **Staff User**: `staff` / `staffpass123`
- **Admin URL**: http://localhost:8000/admin/

These credentials are configured in the `.env` file for development convenience. Use these accounts to access the Django admin interface when testing locally.

### Makefile Commands

**Essential Development Commands:**
- `make dev-safe` - Start development environment with migration validation (recommended)
- `make dev` - Start development environment (basic)
- `make dev-stop` - Stop development environment
- `make dev-restart` - Restart development environment
- `make shell` - Start the Django shell

**Migration Safety Commands:**
- `make makemigrations` - Create new migrations (with validation)
- `make migrate-safe` - Apply migrations with validation and clean environment testing
- `make validate-migrations` - Validate existing migrations for issues
- `make test-migrations-clean` - Test migrations in a clean environment (like CI/CD)

**Developer Workflow Setup:**
- `make setup-dev-workflow` - Set up complete developer workflow with safety enforcement
- `make setup-pre-commit` - Set up complete pre-commit environment for migration safety
- `make pre-commit-install` - Install pre-commit hooks

**Testing & Quality:**
- `make test` - Run tests in Docker
- `make test-local` - Run tests locally (requires local Python environment)
- `make test-in-docker` - Run tests in Docker (for pre-commit hooks)
- `make format` - Format Django templates and Python code

**Utility Commands:**
- `make run` - Run the development server
- `make migrate` - Apply database migrations (basic)
- `make superuser` - Create a superuser
- `make static` - Collect static files
- `make clean` - Remove compiled Python files and caches
- `make publish` - Publish scheduled content
- `make test-schedule` - Create test scheduled content
- `make crontab` - Set up scheduled publishing cron job
- `make prod` - Start production environment
- `make help` - Show all available commands

## Architecture Overview

### Multi-App Django Structure

- **blog/**: Main content with Entry (full posts) and Blogmark (link blog) models
- **til/**: "Today I Learned" short-form content
- **minimalwave-blog/**: Core Django project with modular settings

### Settings Configuration

- **base.py**: Shared settings using environment variables
- **development.py**: PostgreSQL, debug mode, extended apps (allauth, markdownx, taggit)
- **production.py**: PostgreSQL, Redis caching, security hardening, WhiteNoise

### Content Model Architecture

- **BaseEntry**: Abstract base class for all content (title, slug, status, scheduling)
- **Status Workflow**: Draft → Review → Published with scheduled publishing
- **Shared Tagging**: Unified Tag model across all content types
- **Social Media**: Automatic Open Graph and Twitter card generation

### URL Patterns

- Date-based URLs: `/<year>/<month>/<day>/<slug>/`
- Preview URLs for drafts: `/preview/entry/<slug>/` (auth required)
- Separate namespaces for blog and TIL content

### Scheduled Publishing

- **Management Command**: `publish_scheduled` - promotes scheduled content to published
- **Cron Integration**: Production Docker includes automated cron via Supervisor
- **Status Logic**: Finds content with past publish_date in draft/review status

### Database Strategy

- Development: PostgreSQL (matches production for consistency)
- Production: PostgreSQL with SSL and connection pooling
- Migration compatibility maintained across status field changes

### Deployment Architecture

- **Docker Multi-stage**: Poetry dependency management, Gunicorn WSGI
- **Azure App Service**: SSL termination via Azure, Redis Cache integration
- **Static Files**: WhiteNoise with manifest storage for production

## Key Development Patterns

### Content Creation

- All content extends BaseEntry abstract model
- Status field controls visibility (draft/review/published)
- Publish_date enables future scheduling
- Markdown support with automatic HTML rendering

### Template System

- Base template with comprehensive SEO meta tags
- Dark mode minimal wave aesthetic with custom CSS
- Social media sharing optimization
- Responsive design with mobile-first approach

### Admin Interface

- Custom admin configurations for content management
- Preview functionality for draft content
- Publish date management for scheduling

### Testing Approach

- Django test framework via `python manage.py test`
- Pytest support configured
- Utility scripts organized in `scripts/` directory
- Scheduled publishing test utilities
- Make sure to test all new features thoroughly before merging into the main branch.

### Code Quality

- Black formatting (line-length 88, Python 3.10 target)
- isort with Black profile
- Flake8 linting
- Custom Django template formatter

### Commit Guidelines

- Use clear and descriptive commit messages.
- Follow the established commit message format (e.g., `type(scope): subject`).
- Include relevant issue references (e.g., `Fixes #123`).
- Ensure all commits pass tests and adhere to code quality standards.
- Avoid committing sensitive information (e.g., API keys, passwords).
- Make commits atomic, focusing on a single change or feature.
- Regularly pull changes from the main branch to avoid merge conflicts.
- Use rebase instead of merge for a cleaner commit history.
- undo git commit with `git reset --soft HEAD~1` to keep changes staged.
- rollback changes with `git checkout -- <file>` for unstaged changes or `git reset --hard` for all changes.
- test changes before committing to ensure stability.

## Best Practices

### Development Workflow (Safety First)

**Recommended Development Setup:**
1. `make setup-dev-workflow` - Set up complete safety workflow (run once)
2. `make dev-safe` - Always use this over `make dev` for development
3. Use migration safety commands: `make makemigrations`, `make migrate-safe`

**Essential Practices:**
- **Run code in Docker, not locally** - Ensures environment consistency
- **Use safety workflow** - Pre-commit hooks prevent migration issues
- **Always validate migrations** - Use `make validate-migrations` before committing
- **Test in clean environment** - Use `make test-migrations-clean` for CI/CD validation

**Documentation Maintenance:**
- Keep documentation updated with any changes in commands or architecture
- Keep the .env updated with current credentials and settings
- Keep Azure resources file current with latest resource names and configurations
- Use Project Development History for context
- Follow the coding standards and commit guidelines outlined in this document

**When in Doubt:**
- Ask for help if unsure about any changes or commands
- Ask for help if encountering the same error multiple times
- Use the issue tracker to report bugs or request features

c### Database Migration Best Practices

#### Manual Safety Checks
- **ALWAYS check current state before running migrations**: Use `python manage.py showmigrations` to see what migrations exist and their status
- **ONLY run migrations when needed**: Check if there are pending migrations before running `makemigrations` and `migrate`
- **Don't blindly follow setup instructions**: Assess the current state of the project before executing database operations
- **Verify migration necessity**: If git status shows migration files already exist, migrations have likely already been created

#### Automated Safety Workflow (Recommended)
The project now includes automated migration safety measures to prevent CI/CD failures:

**Pre-commit Hooks**: Automatically validate migrations before every commit
```bash
# Set up the complete safety workflow
make setup-pre-commit
```

**Safe Migration Commands**: Use these instead of raw Django commands
```bash
# Create migrations with automatic validation
make makemigrations

# Apply migrations with clean environment testing
make migrate-safe

# Validate existing migrations
make validate-migrations

# Test migrations in CI-like environment
make test-migrations-clean
```

**What the Safety System Prevents**:
- Empty/fake migrations that don't create actual database columns
- Migration dependency conflicts
- Migrations that work locally but fail in CI/CD
- Inconsistent database state between environments

**How It Works**:
1. Pre-commit hooks run migration validation before each commit
2. Scripts check for empty operations, dependency conflicts, and clean environment compatibility
3. Clean environment testing simulates CI/CD conditions locally
4. Validation prevents problematic migrations from reaching production

# Important Troubleshooting Guidelines

## Claude Sandbox Directory
When troubleshooting issues or downloading files for analysis:
- **ALWAYS** use `.claude-sandbox/` directory for temporary files
- This directory is gitignored and safe for debugging artifacts
- Example: When downloading logs, save to `.claude-sandbox/logs.zip`
- Clean up after troubleshooting by deleting downloaded files

## Clean Development Practices
- Never leave zip files, log dumps, or temporary files in the project root
- Use the sandbox directory for any downloaded troubleshooting files
- If you create temporary files outside the sandbox, delete them after use
- Keep the repository clean and professional

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
