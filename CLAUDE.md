---
title: CLAUDE.md
author: Livefront
date: June 2025
output: pdf_document
geometry: margin=1in
papersize: letter
mainfont: Poppins
colorlinks: true
linkcolor: NavyBlue
header-includes:
	- \usepackage{fvextra}
	- \DefineVerbatimEnvironment{Highlighting}{Verbatim}{breaklines,commandchars=\{}}
---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development (Virtual Environment)

```bash
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

# Execute commands in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Makefile Commands

Available via `make <command>`: run, migrate, shell, test, dev, prod, format, static, clean, crontab, superuser, publish, test-schedule

## Architecture Overview

### Multi-App Django Structure

- **blog/**: Main content with Entry (full posts) and Blogmark (link blog) models
- **til/**: "Today I Learned" short-form content
- **minimalwave-blog/**: Core Django project with modular settings

### Settings Configuration

- **base.py**: Shared settings using environment variables
- **development.py**: SQLite, debug mode, extended apps (allauth, markdownx, taggit)
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

- Development: SQLite in `data/db.sqlite3`
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
- Custom test runner script at `run_tests.py`
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

Run the code in Docker, not locally. Use the provided Makefile for convenience in managing common tasks.
Ensure to keep the documentation updated with any changes in commands or architecture. Keep the .env updated. Keep the Azure resources file up to date with the latest resource names and configurations.Use Project Development History. Ask for help if you are unsure about any changes or commands. Ask for help if you encounter the same error multiple times. Use the issue tracker to report bugs or request features. Follow the coding standards and commit guidelines outlined in this document.

### Database Migration Best Practices

- **ALWAYS check current state before running migrations**: Use `python manage.py showmigrations` to see what migrations exist and their status
- **ONLY run migrations when needed**: Check if there are pending migrations before running `makemigrations` and `migrate`
- **Don't blindly follow setup instructions**: Assess the current state of the project before executing database operations
- **Verify migration necessity**: If git status shows migration files already exist, migrations have likely already been created

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
