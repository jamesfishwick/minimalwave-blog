# Build & Deploy Optimization

**Date:** 2026-02-12
**Status:** Approved
**Priority:** Optional Enhancement

## Context

Django application deployed to Azure App Service via GitHub Actions CI/CD. Current deployment is functional but has optimization opportunities for faster builds, better caching, and improved production performance.

## Current Architecture

- **CI/CD:** GitHub Actions workflow (`.github/workflows/ci-cd.yml`)
- **Deployment:** Azure App Service (Linux container)
- **Static Files:** WhiteNoise with manifest storage
- **Database:** PostgreSQL 14 on Azure
- **Build Time:** ~3-5 minutes (uncached)

## Optimization Opportunities

### 1. GitHub Actions Caching

**Problem:** Every build downloads all dependencies from scratch

**Implementation:**

**a) Poetry Dependency Caching**
```yaml
# .github/workflows/ci-cd.yml
jobs:
  build:
    steps:
      - name: Cache Poetry dependencies
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/pypoetry
            .venv
          key: ${{ runner.os }}-poetry-${{ hashFiles('**/poetry.lock') }}
          restore-keys: |
            ${{ runner.os }}-poetry-

      - name: Install dependencies
        run: poetry install --no-interaction --no-ansi
```

**b) Docker Layer Caching**
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ env.REGISTRY }}/minimalwave-blog:latest
    cache-from: type=registry,ref=${{ env.REGISTRY }}/minimalwave-blog:buildcache
    cache-to: type=registry,ref=${{ env.REGISTRY }}/minimalwave-blog:buildcache,mode=max
```

**c) Static File Caching**
```yaml
- name: Cache collectstatic output
  uses: actions/cache@v4
  with:
    path: staticfiles/
    key: ${{ runner.os }}-static-${{ hashFiles('static/**/*') }}
```

**Expected improvement:**
- Build time: 3-5 minutes → 1-2 minutes
- Bandwidth savings: ~200MB per build
- Faster CI feedback loop

---

### 2. Docker Multi-Stage Build Optimization

**Problem:** Large production images with unnecessary build dependencies

**Implementation:**

**Optimized Dockerfile:**
```dockerfile
# Stage 1: Builder
FROM python:3.10-slim as builder

# Install build dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Copy dependency files
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Install dependencies to virtual environment
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-ansi --no-root --only main

# Stage 2: Runtime
FROM python:3.10-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
WORKDIR /app
COPY . .

# Collect static files
ENV PATH="/app/.venv/bin:$PATH"
RUN python manage.py collectstatic --noinput --settings=minimalwave-blog.settings.production

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["gunicorn", "minimalwave-blog.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**Expected improvement:**
- Image size: 800MB → 300MB
- Faster deployments (less data to transfer)
- Reduced security surface (fewer packages)

---

### 3. Azure CDN for Static Files

**Problem:** Static files served from App Service (slower, no global distribution)

**Implementation:**

**a) Azure CDN Setup**
```bash
# Create CDN profile
az cdn profile create \
  --name minimalwave-cdn \
  --resource-group minimalwave-rg \
  --sku Standard_Microsoft

# Create CDN endpoint
az cdn endpoint create \
  --name minimalwave-static \
  --profile-name minimalwave-cdn \
  --resource-group minimalwave-rg \
  --origin minimalwave.azurewebsites.net
```

**b) Django Configuration**
```python
# settings/production.py
STATIC_URL = 'https://minimalwave-static.azureedge.net/static/'

# Optional: Azure Blob Storage for static files
STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
AZURE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT')
AZURE_CONTAINER = 'static'
AZURE_CUSTOM_DOMAIN = 'minimalwave-static.azureedge.net'
```

**c) Cache Headers**
```python
# settings/production.py
WHITENOISE_MAX_AGE = 31536000  # 1 year for static files with hash names
```

**Expected improvement:**
- Global CDN caching (faster for international visitors)
- Reduced App Service bandwidth costs
- Better cache hit rates

---

### 4. Azure App Service Optimization

**Problem:** Default App Service configuration not optimized

**Implementation:**

**a) App Service Plan Scaling**
```bash
# Auto-scaling rules
az monitor autoscale create \
  --resource-group minimalwave-rg \
  --resource minimalwave-app \
  --resource-type Microsoft.Web/serverfarms \
  --name minimalwave-autoscale \
  --min-count 1 \
  --max-count 3 \
  --count 1

# Scale up on CPU >70% for 5 minutes
az monitor autoscale rule create \
  --autoscale-name minimalwave-autoscale \
  --condition "CpuPercentage > 70 avg 5m" \
  --scale out 1
```

**b) Application Settings**
```bash
# Enable HTTP/2
az webapp config set \
  --name minimalwave-app \
  --resource-group minimalwave-rg \
  --http20-enabled true

# Enable always-on (prevent cold starts)
az webapp config set \
  --name minimalwave-app \
  --resource-group minimalwave-rg \
  --always-on true

# Set worker count
az webapp config set \
  --name minimalwave-app \
  --resource-group minimalwave-rg \
  --number-of-workers 2
```

**c) Gunicorn Configuration**
```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000  # Restart workers after 1000 requests (prevent memory leaks)
max_requests_jitter = 50
preload_app = True  # Load app before forking workers
```

**Expected improvement:**
- Better resource utilization
- Automatic scaling under load
- No cold starts (always-on)
- Better concurrency handling

---

### 5. Build Pipeline Optimization

**Problem:** Sequential steps slow down deployment

**Implementation:**

**Parallel Job Execution:**
```yaml
# .github/workflows/ci-cd.yml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10"]
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run linters
        run: |
          black --check .
          isort --check .
          flake8 .

  build-and-deploy:
    needs: [test, lint]  # Only deploy if tests and linting pass
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Build Docker image
        run: docker build -t minimalwave-blog .

      - name: Push to registry
        run: docker push minimalwave-blog

      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: minimalwave-app
          images: ${{ env.REGISTRY }}/minimalwave-blog:latest
```

**Expected improvement:**
- Tests and linting run in parallel
- Faster feedback on failures
- Only deploy if quality gates pass

---

### 6. Database Migration Optimization

**Problem:** Migrations run during deployment (downtime risk)

**Implementation:**

**Zero-Downtime Migrations:**
```yaml
# .github/workflows/ci-cd.yml
- name: Run migrations
  run: |
    # Run migrations before deployment
    az webapp ssh --name minimalwave-app \
      --resource-group minimalwave-rg \
      --command "cd /app && python manage.py migrate --noinput"

- name: Deploy new version
  uses: azure/webapps-deploy@v2
  # Deployment happens after migrations complete
```

**Migration Safety Checks:**
```python
# scripts/check_migrations.py
import sys
from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor

def check_migrations():
    """Verify migrations are safe before deployment"""
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

    # Check for risky operations
    for migration, backwards in plan:
        operations = migration.operations
        for op in operations:
            if isinstance(op, RemoveField):
                print(f"WARNING: {migration} removes field - may break old code")
                sys.exit(1)

    print("Migrations are safe to deploy")

if __name__ == "__main__":
    check_migrations()
```

**Expected improvement:**
- No downtime during deployments
- Migration failures don't break production
- Safer rollback capability

---

## Implementation Checklist

### Phase 1: Quick Wins (No Infrastructure Changes)
- [ ] Enable GitHub Actions dependency caching (Poetry, Docker layers)
- [ ] Optimize Dockerfile with multi-stage build
- [ ] Configure Gunicorn for better concurrency
- [ ] Enable HTTP/2 on App Service
- [ ] Enable always-on to prevent cold starts
- [ ] Add parallel job execution to CI/CD pipeline

### Phase 2: Azure Optimizations
- [ ] Set up Azure CDN for static files
- [ ] Configure auto-scaling rules
- [ ] Optimize App Service plan tier
- [ ] Add Application Insights for monitoring
- [ ] Set up zero-downtime migration workflow

### Phase 3: Advanced Optimizations
- [ ] Azure Blob Storage for static files (optional)
- [ ] Database connection pooling with pgbouncer
- [ ] Redis cache integration (from backend optimizations)
- [ ] Blue/green deployment strategy
- [ ] Automated rollback on health check failure

## Performance Targets

**Current (estimated):**
- Build time: 3-5 minutes
- Deployment time: 2-3 minutes
- Docker image size: 800MB
- Cold start time: 30-60 seconds

**Target (post-optimization):**
- Build time: 1-2 minutes
- Deployment time: 1-2 minutes
- Docker image size: 300MB
- Cold start time: 0 seconds (always-on)

## Cost Implications

- **Azure CDN:** $0.081/GB outbound (first 10TB)
- **Auto-scaling:** Only pay for extra instances when needed
- **Always-on:** Included in Basic tier and above (no extra cost)
- **Application Insights:** $2.30/GB ingested data (free tier: 5GB/month)

## Monitoring

Track these metrics before/after optimization:

- Build duration (GitHub Actions)
- Deployment success rate
- Docker image size (registry metrics)
- Application startup time (Azure metrics)
- Static file cache hit rate (CDN analytics)
- Resource utilization (CPU, memory)

## Dependencies

```txt
# No additional Python dependencies required
# Azure CLI required for CDN setup
```

## Notes

- Phase 1 optimizations have zero cost and immediate impact
- Always-on requires Basic tier App Service plan ($13/month minimum)
- CDN is optional but recommended for global audience
- Auto-scaling prevents over-provisioning while handling traffic spikes
- Multi-stage Docker builds reduce attack surface and deployment time

## Related Documents

- Frontend Performance: `docs/plans/2026-02-12-frontend-performance-optimization.md`
- Backend Performance: `docs/plans/2026-02-12-backend-performance-optimization.md`
- CI/CD Pipeline: `docs/CI-CD-PIPELINE.md`
