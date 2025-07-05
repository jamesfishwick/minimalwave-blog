.PHONY: help run migrate shell test dev prod format static clean crontab superuser

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

test: ## Run tests
	python manage.py test

dev: ## Start development environment with Docker Compose
	docker-compose up -d
	@echo "$(GREEN)Development environment is running at http://localhost:8000$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop following logs (containers will keep running)$(NC)"
	docker-compose logs -f

prod: ## Start production environment with Docker Compose
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Production environment is running at http://localhost:8000$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop following logs (containers will keep running)$(NC)"
	docker-compose -f docker-compose.prod.yml logs -f

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
