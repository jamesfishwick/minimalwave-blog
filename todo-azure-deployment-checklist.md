# Azure Deployment Checklist

This checklist helps ensure a smooth deployment of the Minimal Wave Blog to Azure.

## 1. Pre-Deployment Tasks

- [x] Run tests locally: `make test`
- [x] Check all changes are committed: `git status`
- [x] Push changes to GitHub: `git push origin main`
- [x] Check Docker builds correctly: `docker-compose -f docker-compose.prod.yml build`

## 2. Azure Resources Setup

- [x] Create Resource Group
  ```bash
  az group create --name minimalwave-blog-rg --location eastus
  ```

- [x] Create PostgreSQL Database
  Status: Created minimalwave-blog-db-2025 (Standard_D2s_v3)

- [x] Create Container Registry
  Status: Created minimalwaveregistry.azurecr.io (Basic SKU)

- [x] Create App Service Plan
  Status: Created minimalwave-plan (B1, Linux)

- [x] Create Web App
  Status: Created minimalwave-blog (running container from ACR)

- [ ] Create Redis Cache
  Status: Created minimalwave-cache (Basic C0)

## 3. GitHub Secrets Setup

- [x] `AZURE_CREDENTIALS`: JSON from `az ad sp create-for-rbac`
- [x] `REGISTRY_LOGIN_SERVER`: ACR login server (minimalwaveregistry.azurecr.io)
- [x] `REGISTRY_USERNAME`: ACR username
- [x] `REGISTRY_PASSWORD`: ACR password
- [x] `SECRET_KEY`: Django secret key
- [x] `DATABASE_URL`: PostgreSQL connection string
- [ ] `REDIS_URL`: Redis connection string
- [ ] `REDIS_PASSWORD`: Redis access key

## 4. Environment Variables Setup

- [x] Set Web App environment variables:
  - DJANGO_SETTINGS_MODULE=minimalwave_blog.settings.production
  - SECRET_KEY
  - ALLOWED_HOST
  - DATABASE_URL
  - [ ] REDIS_URL
  - [ ] REDIS_PASSWORD

## 5. Database Firewall Configuration

- [x] Allow Azure services:
  Status: Public network access enabled with firewall rules

## 6. GitHub Actions Workflow

- [x] Verify GitHub Actions workflow file (`.github/workflows/azure-deploy.yml`)
- [x] Trigger deployment manually or by pushing to main branch
- [x] Monitor deployment in GitHub Actions tab

## 7. Post-Deployment Tasks

- [x] Verify the site is running: `https://minimalwave-blog.azurewebsites.net/`
- [x] Create superuser
- [x] Add initial content
- [x] Test scheduled publishing in production
- [x] Set up monitoring alerts

## 8. Optional: Custom Domain Setup

- [ ] Purchase domain (if not already owned)
- [ ] Add custom domain to App Service
- [ ] Configure DNS settings with domain provider
- [x] Set up SSL certificate (documented in docs/ssl-setup.md)
