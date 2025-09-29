.PHONY: help run migrate shell test test-in-docker dev dev-safe dev-stop dev-restart prod format static clean crontab superuser pre-commit-install makemigrations migrate-safe validate-migrations test-migrations-clean setup-pre-commit setup-dev-workflow

# Set default target
.DEFAULT_GOAL := help

# Colors for terminal output
BLUE=\033[0;34m
GREEN=\033[0;32m
RED=\033[0;31m
YELLOW=\033[0;33m
NC=\033[0m # No Color

help: ## Show this help menu
	@echo "Usage: make [TARGET]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

run: ## Run the development server
	python manage.py runserver 0.0.0.0:8000

migrate: ## Apply database migrations
	python manage.py migrate

shell: ## Start the Django shell
	python manage.py shell

test: ## Run tests in Docker
	@cd deploy/docker && docker-compose exec web python manage.py test

test-local: ## Run tests locally (requires local Python environment)
	python manage.py test

test-in-docker: ## Run tests in Docker (for pre-commit hooks)
	@cd deploy/docker && docker-compose exec -T web python manage.py test blog.tests.BlogTestCase.test_blog_entry blog.tests.BlogTestCase.test_blogmark blog.tests.BlogTestCase.test_til_detail

dev: ## Start development environment with Docker Compose (with source code mounting)
	@cd deploy/docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)Development environment is running at http://localhost:8000$(NC)"
	@echo "$(GREEN)Source code is mounted for live changes and migration sync$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop following logs (containers will keep running)$(NC)"
	@cd deploy/docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

dev-safe: validate-migrations ## Start development environment with migration validation
	@echo "$(GREEN)✅ Migrations validated - starting development environment$(NC)"
	@cd deploy/docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)Development environment is running at http://localhost:8000$(NC)"
	@echo "$(GREEN)Source code is mounted for live changes and migration sync$(NC)"

dev-stop: ## Stop development environment
	@cd deploy/docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
	@echo "$(GREEN)Development environment stopped$(NC)"

dev-restart: ## Restart development environment
	@cd deploy/docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
	@cd deploy/docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)Development environment restarted at http://localhost:8000$(NC)"

prod: ## Start production environment with Docker Compose
	@cd deploy/docker && docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Production environment is running at http://localhost:8000$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop following logs (containers will keep running)$(NC)"
	@cd deploy/docker && docker-compose -f docker-compose.prod.yml logs -f

format: ## Format Django templates and Python code
	python format_django_templates.py
	black blog til minimalwave-blog
	isort blog til minimalwave-blog

static: ## Collect static files
	python manage.py collectstatic --noinput

clean: ## Remove compiled Python files and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

crontab: ## Set up scheduled publishing cron job
	./scripts/setup_scheduled_publishing.sh

superuser: ## Create a superuser
	python manage.py createsuperuser

publish: ## Publish scheduled content
	python manage.py publish_scheduled

test-schedule: ## Create test scheduled content (for testing scheduled publishing)
	./scripts/test_scheduling.sh

pre-commit-install: ## Install pre-commit hooks
	pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed successfully!$(NC)"
	@echo "$(YELLOW)Tests will now run before each commit to ensure code quality$(NC)"

# Safe Migration Workflow
makemigrations: validate-migrations ## Create new migrations (with validation)
	@echo "$(YELLOW)Checking development environment...$(NC)"
	./scripts/enforce-dev-environment.sh
	@echo "$(YELLOW)Creating migrations...$(NC)"
	@cd deploy/docker && docker-compose exec web python manage.py makemigrations
	@echo "$(BLUE)Validating new migrations...$(NC)"
	./scripts/validate-migrations.sh
	@echo "$(GREEN)Migrations created and validated successfully!$(NC)"

migrate-safe: validate-migrations ## Apply migrations with validation and clean environment testing
	@echo "$(YELLOW)Running migration safety checks...$(NC)"
	./scripts/validate-migrations.sh
	@echo "$(BLUE)Testing migrations in clean environment...$(NC)"
	./scripts/test-migrations-clean.sh
	@echo "$(GREEN)Migrations applied successfully!$(NC)"

validate-migrations: ## Validate existing migrations for issues
	@echo "$(BLUE)Validating Django migration dependencies...$(NC)"
	./scripts/validate-migrations.sh

test-migrations-clean: ## Test migrations in a clean environment (like CI/CD)
	@echo "$(YELLOW)Testing migrations in clean environment...$(NC)"
	./scripts/test-migrations-clean.sh

setup-pre-commit: ## Set up complete pre-commit environment for migration safety
	@echo "$(BLUE)Setting up pre-commit hooks for migration safety...$(NC)"
	pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed!$(NC)"
	@echo "$(YELLOW)Making validation scripts executable...$(NC)"
	chmod +x scripts/check-migrations.sh scripts/validate-migrations.sh scripts/test-migrations-clean.sh
	@echo "$(GREEN)Migration safety workflow is now active!$(NC)"
	@echo ""
	@echo "$(BLUE)Safe workflow commands:$(NC)"
	@echo "  $(YELLOW)make makemigrations$(NC)     - Create migrations with validation"
	@echo "  $(YELLOW)make migrate-safe$(NC)       - Apply migrations safely"
	@echo "  $(YELLOW)make validate-migrations$(NC) - Check existing migrations"
	@echo "  $(YELLOW)make test-migrations-clean$(NC) - Test in clean environment"

setup-dev-workflow: setup-pre-commit ## Set up complete developer workflow with safety enforcement
	@echo "$(BLUE)Setting up complete developer workflow...$(NC)"
	./scripts/setup-dev-aliases.sh
	@echo "$(GREEN)Developer workflow setup complete!$(NC)"
	@echo ""
	@echo "$(BLUE)🛡️  Safety features enabled:$(NC)"
	@echo "  ✅ Pre-commit hooks for migration validation"
	@echo "  ✅ Shell aliases redirecting unsafe commands"
	@echo "  ✅ Make targets with built-in validation"
	@echo "  ✅ CI/CD pipeline validation"
	@echo ""
	@echo "$(YELLOW)Recommended workflow:$(NC)"
	@echo "  1. $(GREEN)make dev-safe$(NC)           - Start development environment"
	@echo "  2. $(GREEN)safe-migrate$(NC)            - Create and apply migrations safely"
	@echo "  3. $(GREEN)git commit$(NC)              - Pre-commit hooks will validate"
