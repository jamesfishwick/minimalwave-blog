# Azure Blob Storage Troubleshooting Guide

## Issue: Images Not Displaying on Production Site

### Symptoms
- Images uploaded through Django admin show in the admin interface
- But display as broken images on the live site
- Browser console shows 404 errors for blob URLs
- Azure Blob Storage container is empty

### Root Cause
Production App Service is not using Azure Blob Storage due to missing environment variables. Django falls back to local file storage, which is ephemeral (files disappear on container restart).

### Diagnosis Steps

1. **Check if blobs exist in Azure:**
   ```bash
   az storage blob list \
     --account-name minimalwavestorage \
     --container-name media \
     --account-key "<YOUR_KEY>"
   ```
   If this returns empty `[]`, Azure storage is not being used.

2. **Check App Service environment variables:**
   ```bash
   az webapp config appsettings list \
     --name minimalwave-blog \
     --resource-group minimalwave-blog-rg \
     --query "[?name=='AZURE_STORAGE_ACCOUNT_NAME' || name=='AZURE_STORAGE_ACCOUNT_KEY']"
   ```
   If these are missing, files won't upload to Azure.

3. **Verify which settings file is being used:**
   ```bash
   az webapp config appsettings show \
     --name minimalwave-blog \
     --resource-group minimalwave-blog-rg \
     --query "properties.DJANGO_SETTINGS_MODULE"
   ```
   Should be: `minimalwave-blog.settings.production`

## Solution

### Step 1: Fix App Service Configuration

Run the automated fix script:

```bash
./scripts/fix-azure-storage.sh
```

Or manually set environment variables:

```bash
az webapp config appsettings set \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg \
  --settings \
    AZURE_STORAGE_ACCOUNT_NAME="minimalwavestorage" \
    AZURE_STORAGE_ACCOUNT_KEY="<YOUR_KEY>" \
    DJANGO_SETTINGS_MODULE="minimalwave-blog.settings.production"
```

### Step 2: Restart App Service

```bash
az webapp restart \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg
```

### Step 3: Check Existing Images

Run the sync command to identify missing images:

```bash
# In production (via SSH or App Service console)
python manage.py sync_images_to_azure --dry-run
```

This will show:
- ✅ Images that exist in Azure
- ❌ Images that are missing (need re-upload)

### Step 4: Re-upload Missing Images

For each missing image (like your Retna image):

1. Go to Django admin: https://jamesfishwick.com/admin/
2. Find the entry with the missing image
3. Click "Clear" next to the image field
4. Re-upload the image file
5. Save the entry

The image will now upload directly to Azure Blob Storage.

### Step 5: Verify Upload

Check that the blob was created:

```bash
az storage blob list \
  --account-name minimalwavestorage \
  --container-name media \
  --prefix "blog/images/" \
  --account-key "<YOUR_KEY>"
```

You should see your newly uploaded image in the list.

## Prevention

### Ensure These Settings in Production

1. **Environment Variables** (in App Service Configuration):
   ```
   AZURE_STORAGE_ACCOUNT_NAME=minimalwavestorage
   AZURE_STORAGE_ACCOUNT_KEY=<your-key>
   DJANGO_SETTINGS_MODULE=minimalwave-blog.settings.production
   ```

2. **Settings File** (`minimalwave-blog/settings/production.py`):
   ```python
   DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
   AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'
   MEDIA_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/'
   ```

3. **Container Permissions**:
   - Container name: `media`
   - Public access level: `Blob` (allows public read access to blobs)

### Testing After Fix

1. Upload a test image through admin
2. Check it appears in Azure:
   ```bash
   az storage blob list --account-name minimalwavestorage --container-name media
   ```
3. Verify it displays on the site
4. Check browser console for errors

## Common Issues

### Issue: "The specified blob does not exist" (404)
**Cause:** File was never uploaded to Azure
**Fix:** Re-upload through admin after fixing configuration

### Issue: "This request is not authorized" (403)
**Cause:** Wrong container permissions or credentials
**Fix:** Verify AZURE_STORAGE_ACCOUNT_KEY and container is set to `Blob` access

### Issue: Images work locally but not in production
**Cause:** Local uses development.py (local storage), production needs production.py (Azure storage)
**Fix:** Ensure DJANGO_SETTINGS_MODULE=minimalwave-blog.settings.production

### Issue: Container not found
**Cause:** Container doesn't exist in storage account
**Fix:** Create it:
```bash
az storage container create \
  --name media \
  --account-name minimalwavestorage \
  --public-access blob
```

## Useful Commands

### List all blobs
```bash
az storage blob list \
  --account-name minimalwavestorage \
  --container-name media \
  --account-key "<YOUR_KEY>"
```

### Check specific blob
```bash
az storage blob exists \
  --account-name minimalwavestorage \
  --container-name media \
  --name "blog/images/2025/11/filename.jpg" \
  --account-key "<YOUR_KEY>"
```

### Upload blob manually (if needed)
```bash
az storage blob upload \
  --account-name minimalwavestorage \
  --container-name media \
  --name "blog/images/2025/11/filename.jpg" \
  --file /path/to/local/file.jpg \
  --account-key "<YOUR_KEY>"
```

## Quick Fix Summary

For the current issue with the Retna image:

1. ✅ Run: `./scripts/fix-azure-storage.sh`
2. ✅ Restart App Service
3. ✅ Go to admin: https://jamesfishwick.com/admin/blog/entry/{entry-id}/change/
4. ✅ Clear and re-upload the image
5. ✅ Save
6. ✅ Verify image displays on site

The image will now be stored at:
`https://minimalwavestorage.blob.core.windows.net/media/blog/images/2025/11/filename.jpg`
