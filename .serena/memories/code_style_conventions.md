# Code Style and Conventions

## Python Code Style
- **Formatter**: Black (line-length 88, Python 3.10 target)
- **Import Sorting**: isort with Black profile
- **Linting**: Flake8 (max-line-length 88, ignore E203,W503)
- **Security**: Bandit for security checks

## Django Conventions
- **Models**: 
  - Docstrings for all model classes
  - Use `verbose_name` and `verbose_name_plural` in Meta
  - `__str__()` methods for all models
  - Class methods for common queries (e.g., `get_settings()`)
  
- **Settings**:
  - Environment variables via os.getenv() with defaults
  - Modular settings structure (base, development, production, ci)
  - Explicit SECRET_KEY, DEBUG, ALLOWED_HOSTS from env

- **URLs**:
  - Date-based patterns for content: `/<year>/<month>/<day>/<slug>/`
  - Separate namespaces for apps (blog:, til:)
  - Preview URLs require authentication

## File Organization
- **Apps**: Separate Django apps for distinct functionality (blog, til, core, linkedin)
- **Templates**: Base templates in templates/, app-specific in app/templates/
- **Static Files**: Organized in static/ directory
- **Scripts**: Utility scripts in scripts/ directory
- **Tests**: Centralized in tests/ directory
- **Migrations**: Per-app migrations/ directories

## Naming Conventions
- **Python**: snake_case for functions, variables, methods
- **Classes**: PascalCase for class names
- **Constants**: UPPER_CASE for settings and constants
- **Files**: lowercase_with_underscores.py

## Documentation Standards
- Docstrings for all classes and non-trivial functions
- Inline comments for complex logic
- CLAUDE.md for development guidance
- README.md for user-facing documentation