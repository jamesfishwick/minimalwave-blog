# Testing Strategy

## Test Framework
- **Primary**: Django test framework (`python manage.py test`)
- **Alternative**: Pytest (configured and supported)
- **Location**: Centralized in `tests/` directory

## Test Types

### Unit Tests
- **blog tests**: `tests/test_blog.py`
  - Entry model tests
  - Blogmark model tests
  - View tests
  
- **TIL tests**: `tests/test_til.py`
  - TIL model tests
  - View tests

- **Image tests**: `tests/test_images.py`, `tests/test_image_processing.py`
  - Image upload handling
  - Azure Blob Storage integration

### Integration Tests
- **Blog flow**: `tests/test_blog_flow.sh`
  - End-to-end content workflow
  - Status transitions (draft → review → published)

### Manual Tests
- **Playwright**: `tests/manual_playwright_test.py`
  - Browser automation tests
  - UI interaction validation

## Running Tests

### Docker (Recommended)
```bash
make test               # Full test suite in Docker
make test-in-docker    # Specific tests for pre-commit
```

### Local Development
```bash
make test-local        # Requires local Python environment
python manage.py test  # Direct Django test command
pytest                 # Using pytest
```

### Pre-commit Integration
Tests run automatically before commits via pre-commit hooks:
- Django system checks
- Migration validation tests
- Unit test suite (specific critical tests)

## Migration Testing

### Validation Tests
```bash
make validate-migrations     # Check migration integrity
make test-migrations-clean  # Test in clean environment
```

### What Gets Tested
- Empty/fake migration detection
- Dependency graph validation
- Clean environment compatibility (CI/CD simulation)
- Cross-environment consistency

## Test Coverage Areas
- Content model CRUD operations
- Status workflow (draft/review/published)
- Scheduled publishing logic
- URL routing and views
- Admin interface functionality
- Image upload and storage
- Search functionality
- Tag management
- Social media metadata generation

## CI/CD Testing
- GitHub Actions workflow runs tests on push
- Pre-push hooks run comprehensive migration tests
- Production deployment gated on test success