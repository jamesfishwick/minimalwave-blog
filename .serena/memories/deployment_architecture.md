# Deployment Architecture

## Target Platform
**Azure App Service** with containerized deployment

## Docker Architecture

### Multi-stage Build
- **Base Stage**: Poetry dependency management
- **Production Stage**: Gunicorn WSGI server
- **Development Stage**: Debug mode with live code mounting

### Docker Compose Configurations

#### Development (`docker-compose.yml` + `docker-compose.dev.yml`)
- PostgreSQL database container
- Web application with source code volume mounting
- Hot reload for development
- Debug mode enabled
- Port 8000 exposed

#### Production (`docker-compose.prod.yml`)
- PostgreSQL with SSL and connection pooling
- Redis cache container
- Supervisor for process management
- Automated cron for scheduled publishing
- WhiteNoise for static file serving
- Gunicorn WSGI server

## Static Files Strategy
- **Development**: Django's static file serving
- **Production**: WhiteNoise with manifest storage
- **Collection**: `python manage.py collectstatic`
- **Storage**: Azure Blob Storage (django-storages[azure])

## Database Configuration
- **Development**: PostgreSQL (matches production)
- **Production**: PostgreSQL with SSL
- **Connection**: dj-database-url for configuration
- **Migrations**: Automated safety validation

## Caching Strategy
- **Development**: No caching (or local memory)
- **Production**: Redis cache via django-redis
- **Purpose**: Session storage, view caching

## Scheduled Publishing
- **Development**: Manual `make publish` command
- **Production**: Supervisor-managed cron job
- **Frequency**: Hourly execution of `publish_scheduled` command
- **Monitoring**: Logs via Supervisor

## Security Features
- SSL termination via Azure App Service
- HTTPS enforcement in production
- Secure cookie settings
- CSRF protection
- Security middleware enabled
- Bandit security scanning in CI/CD

## Environment Variables
Required for deployment:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode flag (False in production)
- `ALLOWED_HOSTS`: Comma-separated allowed hosts
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (production)
- Azure Blob Storage credentials (for media files)

## CI/CD Pipeline
- **Platform**: GitHub Actions
- **Trigger**: Push to main branch
- **Steps**:
  1. Code checkout
  2. Python setup
  3. Dependency installation
  4. Migration validation
  5. Test execution
  6. Docker image build
  7. Azure deployment
  8. Health check verification

## Deployment Process
1. Code pushed to main branch
2. GitHub Actions workflow triggered
3. Tests and migrations validated
4. Docker image built and pushed
5. Azure App Service updated
6. Application restarted
7. Health check confirms deployment

## Monitoring
- Application logs via Azure App Service
- Supervisor logs for background processes
- Django logging configuration
- Error tracking (configure as needed)