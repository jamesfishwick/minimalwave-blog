.PHONY: help run migrate shell test test-in-docker dev dev-safe dev-stop dev-restart prod format static clean superuser pre-commit-install makemigrations migrate-safe validate-migrations test-migrations-clean check-pending-migrations migration-pre-check setup-pre-commit setup-dev-workflow scheduled-publish-setup scheduled-publish-test publish azure-diagnose azure-fix-storage azure-fix-domain azure-health-check

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

superuser: ## Create a superuser
	python manage.py createsuperuser

# Scheduled Publishing Commands
scheduled-publish-setup: ## Set up cron job for scheduled publishing
	./scripts/scheduled-publishing.sh --setup

scheduled-publish-test: ## Create test scheduled content
	./scripts/scheduled-publishing.sh --test

publish: ## Publish scheduled content now
	./scripts/scheduled-publishing.sh --run

pre-commit-install: ## Install pre-commit hooks
	pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed successfully!$(NC)"
	@echo "$(YELLOW)Tests will now run before each commit to ensure code quality$(NC)"

# Migration Safety Commands
migration-pre-check: ## Pre-flight checklist BEFORE making model changes
	./scripts/migration-safety.sh --pre-check

makemigrations: ## Create new migrations with validation
	@echo "$(YELLOW)Validating before creating migrations...$(NC)"
	./scripts/migration-safety.sh --validate
	@echo "$(YELLOW)Creating migrations...$(NC)"
	@cd deploy/docker && docker-compose exec web python manage.py makemigrations
	@echo "$(BLUE)Validating new migrations...$(NC)"
	./scripts/migration-safety.sh --validate
	@echo "$(GREEN)Migrations created and validated successfully!$(NC)"

migrate-safe: ## Apply migrations with full safety checks
	./scripts/migration-safety.sh --all

validate-migrations: ## Validate existing migrations
	./scripts/migration-safety.sh --validate

test-migrations-clean: ## Test migrations in clean environment
	./scripts/migration-safety.sh --test-clean

check-pending-migrations: ## Check for pending migrations
	./scripts/migration-safety.sh --check-pending

# Azure Operations Commands
azure-diagnose: ## Diagnose production issues (download logs)
	./scripts/azure-ops.sh --diagnose

azure-fix-storage: ## Fix Azure storage configuration
	./scripts/azure-ops.sh --fix-storage

azure-fix-domain: ## Fix Site domain configuration
	./scripts/azure-ops.sh --fix-domain

azure-health-check: ## Run comprehensive Azure health check
	./scripts/azure-ops.sh --health-check

# Developer Setup Commands
setup-dev-workflow: ## Complete dev environment setup (run once)
	./scripts/setup-dev-environment.sh

setup-pre-commit: ## Set up pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	pre-commit install
	pre-commit install --hook-type pre-push
	@echo "$(GREEN)Pre-commit hooks installed!$(NC)"
