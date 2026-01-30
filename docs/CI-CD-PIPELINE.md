# CI/CD Pipeline Documentation

**Single Source of Truth for Deployment**

This document describes the automated CI/CD pipeline for the Minimal Wave Blog project.

## Table of Contents

- [Overview](#overview)
- [Workflow Triggers](#workflow-triggers)
- [Pipeline Jobs](#pipeline-jobs)
- [Success Criteria](#success-criteria)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Rollback Procedures](#rollback-procedures)

---

## Overview

**Unified Pipeline:** `.github/workflows/ci-cd.yml`

**Philosophy:**
- **Validate everything before deployment** - No code reaches production without passing all checks
- **PostgreSQL testing** - CI environment matches production database
- **Conditional deployment** - Only deploys on push to main branch
- **Automated smoke tests** - Verify deployment succeeded

**Flow:**
```
Push/PR → Job 1: Validate & Test (PostgreSQL) → Job 2: Build & Deploy (main only) → Smoke Tests
```

---

## Workflow Triggers

### Automatic Triggers

1. **Push to main or develop branches**
   - Runs: Job 1 (Validate & Test) + Job 2 (Build & Deploy, main only)
   - Use: Automated deployment after merge

2. **Pull requests to main or develop**
   - Runs: Job 1 (Validate & Test) only
   - Use: Validate code before merge

3. **Manual trigger (workflow_dispatch)**
   - Runs: Job 1 + Job 2 (if on main branch)
   - Use: Manual deployment or testing

### What Triggers Deployment?

**Deployment ONLY happens when:**
- Event is `push` (not PR)
- Branch is `main`
- Job 1 (Validate & Test) passes

**Deployment NEVER happens for:**
- Pull requests (validation only)
- Pushes to develop branch (validation only)
- Failed validation/tests

---

## Pipeline Jobs

### Job 1: Validate & Test

**Purpose:** Ensure code quality and migration safety

**Environment:**
- Ubuntu latest
- Python 3.10
- PostgreSQL 14 (matches production)

**Steps:**

1. **Setup**
   - Checkout code
   - Set up Python 3.10
   - Install Poetry
   - Cache Poetry dependencies
   - Install dependencies (`poetry install`)

2. **Migration Validation**
   - Validate migration dependencies
   - Check for uncommitted migrations
   - Check for migration conflicts
   - Verify migration consistency

3. **Django System Checks**
   - Run deployment checks (`--deploy` flag)
   - Catch configuration issues

4. **Clean Environment Testing**
   - Apply migrations from scratch
   - Verify database schema
   - Ensure migrations work in fresh environment

5. **Test Suite**
   - Run all Django tests
   - Ensure 80%+ coverage

**Duration:** ~5-8 minutes

**Failure Conditions:**
- Migration validation fails
- Pending uncommitted migrations
- Migration conflicts detected
- Django check fails
- Migrations fail to apply
- Tests fail

---

### Job 2: Build & Deploy

**Purpose:** Build Docker image and deploy to Azure

**Conditional:** Only runs on push to main after Job 1 passes

**Environment:**
- Ubuntu latest
- Azure CLI
- Docker buildx

**Steps:**

1. **Azure Login**
   - Authenticate using `AZURE_CREDENTIALS` secret
   - Access Azure Container Registry

2. **Docker Build**
   - Platform: `linux/amd64` (Azure compatibility)
   - Tags: `<registry>/minimalwave-blog:<sha>` and `latest`
   - Settings: `minimalwave-blog.settings.production`
   - Dockerfile: `deploy/docker/Dockerfile`

3. **Docker Push**
   - Push to Azure Container Registry
   - Both `<sha>` and `latest` tags

4. **Deploy to Azure App Service**
   - App: `minimalwave-blog`
   - Image: `<registry>/minimalwave-blog:<sha>`
   - Azure handles service restart

5. **Stabilization Wait**
   - Wait 45 seconds for deployment
   - Allow containers to start

6. **Smoke Tests**
   - Test homepage: `https://jamesfishwick.com/`
   - Test blog post: `https://jamesfishwick.com/2025/jul/2/...`
   - Test admin: `https://jamesfishwick.com/admin/`
   - 3 retries with 10-second delays

7. **Cleanup**
   - Azure logout (always runs)

**Duration:** ~8-12 minutes

**Failure Conditions:**
- Docker build fails
- Docker push fails
- Azure deployment fails
- Smoke tests fail (all 3 retries)

---

## Success Criteria

### Validation Success

✅ **All checks must pass:**
- Migration validation clean
- No pending uncommitted migrations
- No migration conflicts
- Django deployment checks pass
- Migrations apply successfully from scratch
- All tests pass

### Deployment Success

✅ **All steps must succeed:**
- Docker image builds without errors
- Image pushed to registry
- Azure deployment completes
- App Service restarts successfully
- Homepage returns 200 OK
- Blog post returns 200 OK
- Admin interface returns 200 OK

---

## Monitoring

### GitHub Actions

**View workflow runs:**
```
https://github.com/<your-org>/minimalwave-blog/actions
```

**Check specific run:**
- Click on workflow run
- Review job logs
- Check step outputs

### Azure Monitoring

**App Service logs:**
```bash
# View recent logs
az webapp log tail \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg

# Download full logs
az webapp log download \
  --resource-group minimalwave-blog-rg \
  --name minimalwave-blog \
  --log-file logs.zip
```

**Health check:**
```bash
make azure-health-check
```

**Diagnose issues:**
```bash
make azure-diagnose
```

### Site Monitoring

**Manual checks:**
```bash
# Homepage
curl -I https://jamesfishwick.com/

# Admin
curl -I https://jamesfishwick.com/admin/

# Specific blog post
curl -I https://jamesfishwick.com/2025/jul/2/model-autophagy-disorder-ai-will-eat-itself/
```

---

## Troubleshooting

### Migration Validation Failures

**Problem:** "Migration conflicts detected"

**Solution:**
```bash
# Check migration state
python manage.py showmigrations

# Fix conflicts locally
python manage.py makemigrations --merge

# Test in clean environment
make test-migrations-clean
```

---

**Problem:** "Pending uncommitted migrations"

**Solution:**
```bash
# Check what migrations would be created
python manage.py makemigrations --dry-run

# Create migrations
make makemigrations

# Commit migrations
git add */migrations/*.py
git commit -m "feat: Add migrations for <change>"
```

---

### Docker Build Failures

**Problem:** "poetry install failed"

**Solution:**
```bash
# Check poetry.lock is committed
git status poetry.lock

# Regenerate lock file
poetry lock

# Commit changes
git add poetry.lock
git commit -m "chore: Update poetry.lock"
```

---

**Problem:** "Docker build timeout"

**Solution:**
- Check Dockerfile for inefficiencies
- Ensure `.dockerignore` excludes unnecessary files
- Use Docker layer caching effectively

---

### Deployment Failures

**Problem:** "Azure deployment failed"

**Solution:**
```bash
# Check Azure App Service status
make azure-health-check

# View deployment logs
make azure-diagnose

# Check environment variables
az webapp config appsettings list \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg
```

---

**Problem:** "Smoke tests failing (all retries)"

**Solution:**
```bash
# Check if site is actually down
curl -I https://jamesfishwick.com/

# Download logs
make azure-diagnose

# Check for migration issues in production
az webapp ssh \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg

# Then: python manage.py showmigrations
```

---

### Azure Storage Issues

**Problem:** "Images not displaying (404 errors)"

**Solution:**
```bash
# Fix storage configuration
make azure-fix-storage

# Re-upload images through Django admin
# Or use sync command
python manage.py sync_images_to_azure
```

**Documentation:** See `docs/AZURE_STORAGE_TROUBLESHOOTING.md`

---

### Site Domain Issues

**Problem:** "Site domain shows example.com in admin"

**Solution:**
```bash
# Fix domain configuration
make azure-fix-domain

# Or manually via Azure SSH
az webapp ssh --name minimalwave-blog --resource-group minimalwave-blog-rg
# Then: python manage.py shell
# from django.contrib.sites.models import Site
# site = Site.objects.get(id=1)
# site.domain = 'jamesfishwick.com'
# site.save()
```

---

## Best Practices

### Before Pushing Code

1. **Run validation locally:**
   ```bash
   make validate-migrations
   make test
   ```

2. **Test in clean environment:**
   ```bash
   make test-migrations-clean
   ```

3. **Check for pending migrations:**
   ```bash
   make check-pending-migrations
   ```

### Working with Migrations

1. **Before modifying models:**
   ```bash
   # Pre-flight checklist
   make migration-pre-check
   ```

2. **Creating migrations:**
   ```bash
   # Use safe workflow
   make makemigrations
   ```

3. **Applying migrations locally:**
   ```bash
   # Full safety checks
   make migrate-safe
   ```

4. **Testing migrations:**
   ```bash
   # Simulate CI environment
   make test-migrations-clean
   ```

### Code Review

**Reviewer checklist:**
- [ ] All tests pass locally
- [ ] Migrations validated
- [ ] No pending uncommitted migrations
- [ ] CI/CD pipeline passes
- [ ] Deployment smoke tests pass

### Deployment

**Merge strategy:**
1. Create feature branch from `main`
2. Make changes and commit
3. Push to remote (triggers PR validation)
4. Create pull request
5. Wait for CI checks to pass
6. Review and approve
7. Merge to main (triggers deployment)
8. Monitor deployment logs
9. Verify smoke tests pass
10. Check production site

---

## Rollback Procedures

### Quick Rollback (Deploy Previous Version)

**Re-deploy last working commit:**
```bash
# Find last working commit
git log --oneline

# Push to main to trigger deployment
git reset --hard <working-commit-sha>
git push origin main --force
```

**Or manually via Azure:**
```bash
# List recent deployments
az webapp deployment list \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg

# Rollback to specific deployment
az webapp deployment slot swap \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg \
  --slot staging
```

---

### Migration Rollback

**If migrations break production:**

1. **SSH into Azure App Service:**
   ```bash
   az webapp ssh \
     --name minimalwave-blog \
     --resource-group minimalwave-blog-rg
   ```

2. **Rollback migrations:**
   ```bash
   # Check current state
   python manage.py showmigrations

   # Rollback to specific migration
   python manage.py migrate <app> <migration_number>

   # Example:
   python manage.py migrate blog 0002
   ```

3. **Restart App Service:**
   ```bash
   az webapp restart \
     --name minimalwave-blog \
     --resource-group minimalwave-blog-rg
   ```

---

### Emergency Procedures

**Site is completely down:**

1. **Check Azure status:**
   ```bash
   make azure-health-check
   ```

2. **Download logs:**
   ```bash
   make azure-diagnose
   ```

3. **Restart App Service:**
   ```bash
   az webapp restart \
     --name minimalwave-blog \
     --resource-group minimalwave-blog-rg
   ```

4. **If restart doesn't help, rollback:**
   ```bash
   # Deploy last known good version
   git reset --hard <last-good-commit>
   git push origin main --force
   ```

5. **Monitor deployment:**
   - Watch GitHub Actions workflow
   - Check smoke tests pass
   - Verify site is accessible

---

## Configuration Reference

### Required GitHub Secrets

**For Azure deployment:**
- `AZURE_CREDENTIALS` - Azure service principal JSON
- `REGISTRY_LOGIN_SERVER` - Azure Container Registry URL
- `REGISTRY_USERNAME` - ACR username
- `REGISTRY_PASSWORD` - ACR password

**Setting secrets:**
```
GitHub > Settings > Secrets and variables > Actions > New repository secret
```

### Environment Variables (Azure App Service)

**Required settings:**
```bash
# Django
DJANGO_SETTINGS_MODULE=minimalwave-blog.settings.production
SECRET_KEY=<production-secret-key>

# Database
DATABASE_URL=<postgresql-connection-string>

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=<storage-account>
AZURE_STORAGE_ACCOUNT_KEY=<storage-key>

# Site
ALLOWED_HOSTS=jamesfishwick.com,.azurewebsites.net
```

**Check current settings:**
```bash
az webapp config appsettings list \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg
```

---

## Architecture Diagrams

### CI/CD Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Developer pushes to main                                        │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Job 1: Validate & Test (PostgreSQL 14)                          │
│ ─────────────────────────────────────────                       │
│ • Validate migration dependencies                               │
│ • Check for pending migrations                                  │
│ • Run Django system checks                                      │
│ • Apply migrations in clean environment                         │
│ • Run test suite                                                │
└─────────────────┬───────────────────────────────────────────────┘
                  │ ✅ Pass
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Job 2: Build & Deploy (main branch only)                        │
│ ─────────────────────────────────────────                       │
│ • Build Docker image (linux/amd64)                              │
│ • Push to Azure Container Registry                              │
│ • Deploy to Azure App Service                                   │
│ • Wait for stabilization (45s)                                  │
│ • Run smoke tests (homepage, blog, admin)                       │
└─────────────────┬───────────────────────────────────────────────┘
                  │ ✅ Pass
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ ✅ Deployment Complete - Site Live                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- **Development Guide:** `CLAUDE.md`
- **Azure Deployment:** `docs/azure-deployment.md`
- **Azure Storage:** `docs/AZURE_STORAGE_TROUBLESHOOTING.md`
- **Scripts Reference:** `scripts/README.md`

---

## Support

**Getting help:**
1. Check this documentation first
2. Review GitHub Actions logs
3. Run `make azure-diagnose` for production issues
4. Check Azure Application Insights for errors
5. Contact DevOps team if issue persists

**Useful commands:**
```bash
make help                  # Show all available commands
make azure-health-check    # Check Azure resources
make azure-diagnose        # Download and analyze logs
make validate-migrations   # Validate migrations locally
make test-migrations-clean # Test in clean environment
```
