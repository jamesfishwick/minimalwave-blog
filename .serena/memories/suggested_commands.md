# Essential Development Commands

## Quick Start (Recommended)
```bash
# Start development environment with safety checks
make dev-safe

# Access admin interface
# URL: http://localhost:8000/admin/
# Admin: admin / adminpass123
# Staff: staff / staffpass123
```

## Development Workflow

### Docker Development (Primary Method)
```bash
make dev-safe              # Start with migration validation (recommended)
make dev                   # Start basic development environment
make dev-stop             # Stop development environment
make dev-restart          # Restart development environment
make shell                # Django shell in container
```

### Database Operations
```bash
make makemigrations       # Create migrations with validation
make migrate-safe         # Apply migrations with safety checks
make validate-migrations  # Validate existing migrations
make test-migrations-clean # Test in clean environment (CI-like)
```

### Testing & Quality
```bash
make test                 # Run tests in Docker
make test-local          # Run tests locally (requires venv)
make format              # Format templates and Python code
```

### Content Management
```bash
make publish             # Publish scheduled content
make test-schedule       # Create test scheduled content
make superuser           # Create superuser account
```

### Utility Commands
```bash
make run                 # Run development server
make static              # Collect static files
make clean               # Remove Python cache files
make help                # Show all available commands
```

## Local Development (Alternative)
```bash
# Virtual environment setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database operations
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver 0.0.0.0:8000

# Code formatting
black blog til minimalwave-blog
isort blog til minimalwave-blog
python format_django_templates.py
```

## Production Environment
```bash
make prod                # Start production environment
```

## Darwin (macOS) System Commands
- `ls` - List directory contents
- `find` - Search for files
- `grep` - Search text patterns
- `git` - Version control
- Standard Unix commands available