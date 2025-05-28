# Azure Deployment Guide for Minimal Wave Blog

This guide provides instructions for deploying the Minimal Wave Blog to Azure App Service with a PostgreSQL database.

## Prerequisites

1. An Azure account
2. Azure CLI installed locally or use Azure Cloud Shell
3. Git installed locally

## Step 1: Create Azure Resources

### Create a Resource Group

```bash
az group create --name minimalwave-blog-rg --location eastus
```

### Create a PostgreSQL Database

```bash
az postgres flexible-server create \
  --resource-group minimalwave-blog-rg \
  --name minimalwave-db \
  --admin-user minimalwave \
  --admin-password <your-secure-password> \
  --sku-name Standard_B1ms \
  --version 14
```

Create a database:

```bash
az postgres flexible-server db create \
  --resource-group minimalwave-blog-rg \
  --server-name minimalwave-db \
  --database-name minimalwave
```

### Create an App Service Plan

```bash
az appservice plan create \
  --resource-group minimalwave-blog-rg \
  --name minimalwave-plan \
  --sku B1 \
  --is-linux
```

### Create a Web App

```bash
az webapp create \
  --resource-group minimalwave-blog-rg \
  --plan minimalwave-plan \
  --name minimalwave-blog \
  --runtime "PYTHON:3.10" \
  --deployment-local-git
```

## Step 2: Configure Environment Variables

Set the necessary environment variables for your Django application:

```bash
az webapp config appsettings set \
  --resource-group minimalwave-blog-rg \
  --name minimalwave-blog \
  --settings \
    DJANGO_SETTINGS_MODULE=minimalwave-blog.settings.production \
    SECRET_KEY="<your-secret-key>" \
    ALLOWED_HOST="minimalwave-blog.azurewebsites.net" \
    DATABASE_URL="postgres://minimalwave:<your-secure-password>@minimalwave-db.postgres.database.azure.com:5432/minimalwave"
```

## Step 3: Configure Database Firewall

Allow connections from Azure services:

```bash
az postgres flexible-server firewall-rule create \
  --resource-group minimalwave-blog-rg \
  --name minimalwave-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

## Step 4: Prepare Your Local Project for Deployment

1. Create a `.env` file in your project root (do not commit this to version control):

```
SECRET_KEY=<your-secret-key>
DATABASE_URL=postgres://minimalwave:<your-secure-password>@minimalwave-db.postgres.database.azure.com:5432/minimalwave
ALLOWED_HOST=minimalwave-blog.azurewebsites.net
```

2. Create a `startup.sh` file in your project root:

```bash
#!/bin/bash

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Start Gunicorn
gunicorn minimalwave-blog.wsgi:application --bind=0.0.0.0:8000
```

3. Make the startup script executable:

```bash
chmod +x startup.sh
```

4. Create a `.deployment` file in your project root:

```
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

## Step 5: Deploy Your Application

### Option 1: Deploy with Git

1. Add the Azure remote to your Git repository:

```bash
git remote add azure <deployment-local-git-url>
```

2. Push your code to Azure:

```bash
git push azure main
```

### Option 2: Deploy with GitHub Actions

1. Create a `.github/workflows/azure-deploy.yml` file:

```yaml
name: Deploy to Azure

on:
  push:
    branches:
      - main

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Collect static files
      run: python manage.py collectstatic --noinput
      env:
        DJANGO_SETTINGS_MODULE: minimalwave-blog.settings.production
        SECRET_KEY: ${{ secrets.SECRET_KEY }}
        DATABASE_URL: ${{ secrets.DATABASE_URL }}

    - name: Deploy to Azure
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'minimalwave-blog'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

2. Add the necessary secrets to your GitHub repository:
   - `SECRET_KEY`: Your Django secret key
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `AZURE_WEBAPP_PUBLISH_PROFILE`: Your Azure Web App publish profile

## Step 6: Configure Custom Domain (Optional)

1. Purchase a domain name from a domain registrar
2. Add a custom domain to your Azure Web App:

```bash
az webapp config hostname add \
  --resource-group minimalwave-blog-rg \
  --webapp-name minimalwave-blog \
  --hostname www.yourdomainname.com
```

3. Configure DNS settings with your domain registrar:
   - Add a CNAME record pointing to `minimalwave-blog.azurewebsites.net`

## Step 7: Enable HTTPS (Optional)

1. Create a managed certificate:

```bash
az webapp config ssl create \
  --resource-group minimalwave-blog-rg \
  --name minimalwave-blog \
  --hostname www.yourdomainname.com
```

2. Bind the certificate to your web app:

```bash
az webapp config ssl bind \
  --resource-group minimalwave-blog-rg \
  --name minimalwave-blog \
  --certificate-thumbprint <certificate-thumbprint> \
  --ssl-type SNI
```

## Troubleshooting

- Check application logs: `az webapp log tail --resource-group minimalwave-blog-rg --name minimalwave-blog`
- SSH into the web app: `az webapp ssh --resource-group minimalwave-blog-rg --name minimalwave-blog`
- Check deployment logs in the Azure Portal under your web app's Deployment Center

## Maintenance

- Update your application: Push new commits to the deployment branch
- Scale your app service plan if needed: `az appservice plan update --resource-group minimalwave-blog-rg --name minimalwave-plan --sku S1`
- Create database backups: `az postgres flexible-server backup create --resource-group minimalwave-blog-rg --server-name minimalwave-db`
