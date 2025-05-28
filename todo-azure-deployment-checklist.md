# Azure Deployment Checklist

This checklist helps ensure a smooth deployment of the Minimal Wave Blog to Azure.

## 1. Pre-Deployment Tasks

- [ ] Run tests locally: `make test`
- [ ] Check all changes are committed: `git status`
- [ ] Push changes to GitHub: `git push origin main`
- [ ] Check Docker builds correctly: `docker-compose -f docker-compose.prod.yml build`

## 2. Azure Resources Setup

- [ ] Create Resource Group
  ```bash
  az group create --name minimalwave-blog-rg --location eastus
  ```

- [ ] Create PostgreSQL Database
  ```bash
  az postgres flexible-server create \
    --resource-group minimalwave-blog-rg \
    --name minimalwave-db \
    --admin-user minimalwave \
    --admin-password <your-secure-password> \
    --sku-name Standard_B1ms
  
  az postgres flexible-server db create \
    --resource-group minimalwave-blog-rg \
    --server-name minimalwave-db \
    --database-name minimalwave
  ```

- [ ] Create Container Registry
  ```bash
  az acr create \
    --resource-group minimalwave-blog-rg \
    --name minimalwaveregistry \
    --sku Basic
  ```

- [ ] Create App Service Plan
  ```bash
  az appservice plan create \
    --resource-group minimalwave-blog-rg \
    --name minimalwave-plan \
    --is-linux \
    --sku B1
  ```

- [ ] Create Web App
  ```bash
  az webapp create \
    --resource-group minimalwave-blog-rg \
    --plan minimalwave-plan \
    --name minimalwave-blog \
    --deployment-container-image-name minimalwaveregistry.azurecr.io/minimalwave-blog:latest
  ```

## 3. GitHub Secrets Setup

Add these secrets to your GitHub repository:

- [ ] `AZURE_CREDENTIALS`: JSON from `az ad sp create-for-rbac`
- [ ] `REGISTRY_LOGIN_SERVER`: ACR login server (e.g., `minimalwaveregistry.azurecr.io`)
- [ ] `REGISTRY_USERNAME`: ACR username
- [ ] `REGISTRY_PASSWORD`: ACR password
- [ ] `SECRET_KEY`: Django secret key
- [ ] `DATABASE_URL`: PostgreSQL connection string

## 4. Environment Variables Setup

- [ ] Set Web App environment variables:
  ```bash
  az webapp config appsettings set \
    --resource-group minimalwave-blog-rg \
    --name minimalwave-blog \
    --settings \
      DJANGO_SETTINGS_MODULE=minimalwave-blog.settings.production \
      SECRET_KEY="<your-secret-key>" \
      ALLOWED_HOST="minimalwave-blog.azurewebsites.net" \
      DATABASE_URL="postgres://minimalwave:<password>@minimalwave-db.postgres.database.azure.com:5432/minimalwave"
  ```

## 5. Database Firewall Configuration

- [ ] Allow Azure services:
  ```bash
  az postgres flexible-server firewall-rule create \
    --resource-group minimalwave-blog-rg \
    --name minimalwave-db \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0
  ```

## 6. GitHub Actions Workflow

- [ ] Verify GitHub Actions workflow file (`.github/workflows/azure-deploy.yml`)
- [ ] Trigger deployment manually or by pushing to main branch
- [ ] Monitor deployment in GitHub Actions tab

## 7. Post-Deployment Tasks

- [ ] Verify the site is running: `https://minimalwave-blog.azurewebsites.net/`
- [ ] Create superuser (if not created automatically)
  ```bash
  az webapp ssh --resource-group minimalwave-blog-rg --name minimalwave-blog
  # Inside SSH session:
  python manage.py createsuperuser
  ```
- [ ] Add initial content
- [ ] Test scheduled publishing in production
- [ ] Set up monitoring alerts

## 8. Optional: Custom Domain Setup

- [ ] Purchase domain (if not already owned)
- [ ] Add custom domain to App Service:
  ```bash
  az webapp config hostname add \
    --resource-group minimalwave-blog-rg \
    --webapp-name minimalwave-blog \
    --hostname www.yourdomain.com
  ```
- [ ] Configure DNS settings with domain provider
- [ ] Set up SSL certificate
