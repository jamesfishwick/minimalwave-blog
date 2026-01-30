#!/bin/bash
# Fix Azure Blob Storage Configuration for Production

set -e

echo "========================================="
echo "Azure Storage Configuration Fixer"
echo "========================================="
echo ""

# Source the Azure resources file for credentials
if [ -f ".azure-resources" ]; then
    source .azure-resources
else
    echo "Error: .azure-resources file not found"
    exit 1
fi

APP_NAME="minimalwave-blog"
RESOURCE_GROUP="minimalwave-blog-rg"

echo "1. Checking current App Service environment variables..."
echo ""

CURRENT_VARS=$(az webapp config appsettings list \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[?name=='AZURE_STORAGE_ACCOUNT_NAME' || name=='AZURE_STORAGE_ACCOUNT_KEY'].{name:name, value:value}" \
    -o table)

echo "$CURRENT_VARS"
echo ""

echo "2. Setting Azure Storage environment variables..."
echo ""

az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        AZURE_STORAGE_ACCOUNT_NAME="$AZURE_STORAGE_ACCOUNT_NAME" \
        AZURE_STORAGE_ACCOUNT_KEY="$AZURE_STORAGE_KEY" \
    --output table

echo ""
echo "3. Verifying Django settings file..."
echo "   Ensure DJANGO_SETTINGS_MODULE=minimalwave-blog.settings.production"
echo ""

az webapp config appsettings show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.DJANGO_SETTINGS_MODULE" \
    -o tsv

echo ""
echo "========================================="
echo "✅ Configuration Updated!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Restart your App Service:"
echo "   az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "2. Re-upload the image through Django admin"
echo "   URL: https://jamesfishwick.com/admin/"
echo ""
echo "3. Verify the blob was created:"
echo "   az storage blob list --account-name minimalwavestorage --container-name media"
echo ""
