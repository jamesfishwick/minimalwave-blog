# Project Structure

## Top-Level Organization
```
minimalwave-blog/
├── minimalwave-blog/     # Core Django project
│   ├── settings/         # Modular settings (base, dev, prod, ci)
│   ├── urls.py           # Root URL configuration
│   ├── wsgi.py           # WSGI application
│   └── asgi.py           # ASGI application
├── blog/                 # Blog app (Entry, Blogmark models)
│   ├── models.py         # Content models
│   ├── views.py          # View logic
│   ├── urls.py           # URL patterns
│   ├── admin.py          # Admin configuration
│   ├── migrations/       # Database migrations
│   ├── management/       # Custom commands (publish_scheduled)
│   └── utils/            # Utility functions
├── til/                  # TIL (Today I Learned) app
│   ├── models.py         # TIL model
│   ├── views.py          # View logic
│   ├── urls.py           # URL patterns
│   ├── admin.py          # Admin configuration
│   └── migrations/       # Database migrations
├── core/                 # Core/shared functionality
│   └── models.py         # Shared models (taxonomy, etc.)
├── linkedin/             # LinkedIn integration app
├── templates/            # Base templates
├── static/               # Static files (CSS, images)
├── staticfiles/          # Collected static files (production)
├── media/                # User-uploaded files
├── tests/                # Test suite
│   ├── test_blog.py      # Blog app tests
│   ├── test_til.py       # TIL app tests
│   └── test_images.py    # Image handling tests
├── scripts/              # Utility scripts
│   ├── validate-migrations.sh
│   ├── test-migrations-clean.sh
│   └── setup_scheduled_publishing.sh
├── deploy/               # Deployment configurations
│   └── docker/           # Docker compose files
├── docs/                 # Documentation
├── .github/              # GitHub Actions workflows
├── manage.py             # Django management script
├── Makefile              # Development commands
├── pyproject.toml        # Poetry dependencies & tool config
├── requirements.txt      # Pip requirements
├── CLAUDE.md             # Claude Code guidance
└── README.md             # User documentation
```

## Key Directories

### Apps
- **blog/**: Main blog entries and blogmarks (link blog)
- **til/**: Today I Learned short-form content
- **core/**: Shared models and utilities
- **linkedin/**: LinkedIn integration features

### Configuration
- **minimalwave-blog/settings/**: Environment-specific settings
  - base.py: Shared configuration
  - development.py: Local development (DEBUG=True, extended apps)
  - production.py: Production (Redis, security, WhiteNoise)
  - ci.py: CI/CD pipeline settings

### Testing
- **tests/**: Centralized test suite
- **scripts/**: Safety and utility scripts
- **.github/**: CI/CD workflows

### Deployment
- **deploy/docker/**: Docker and Docker Compose configurations
- **Dockerfile**: Production image definition
- **docker-compose.yml**: Development environment
- **docker-compose.dev.yml**: Development overrides
- **docker-compose.prod.yml**: Production environment