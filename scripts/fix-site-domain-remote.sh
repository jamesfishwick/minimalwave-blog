#!/bin/bash
# Fix Django Site domain remotely via Azure Container Instances

echo "🔧 Fixing Django Site domain on production..."

# Use Azure CLI to execute the management command
az container exec \
  --resource-group minimalwave-blog-rg \
  --name minimalwave-blog \
  --exec-command "python manage.py fix_site_domain"

echo "✅ Site domain fix command executed"