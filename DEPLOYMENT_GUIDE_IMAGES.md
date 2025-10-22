# Image Support Deployment Guide
## Azure Blob Storage Implementation - Ready for Production

---

## Pre-Deployment Checklist

### ✅ Completed Code Changes
- [x] Added `django-storages[azure]` to `pyproject.toml`
- [x] Configured `production.py` for Azure Blob Storage
- [x] Updated `.env` with storage credentials (placeholder)
- [x] Documented resources in `.azure-resources`
- [x] Created database migrations for image fields

### 🔲 Required Manual Steps (Do Before Deploying)

#### 1. Create Azure Storage Account
**Via Azure Portal**: https://portal.azure.com

1. Search "Storage accounts" → "Create"
2. Fill in:
   - **Resource Group**: `minimalwave-blog-rg`
   - **Storage Account Name**: `minimalwavestorage`
   - **Region**: `East US`
   - **Performance**: Standard
   - **Redundancy**: LRS
3. Click "Review + Create" → "Create" (wait 1-2 minutes)

#### 2. Create Media Container
After storage account is created:

1. Go to storage account → Left menu: "Containers"
2. Click "+ Container"
3. Settings:
   - **Name**: `media`
   - **Public access level**: Private
4. Click "Create"

#### 3. Get Storage Account Key
1. Storage account → Left menu: "Access keys"
2. Click "Show" next to key1
3. Copy the **Key** value (long base64 string)

#### 4. Update .env File
Replace placeholder in `.env`:
```bash
AZURE_STORAGE_ACCOUNT_KEY=<paste-your-key-here>
```

#### 5. Configure Azure App Service Environment Variables

**Option A: Azure Portal**
1. Go to: https://portal.azure.com
2. Navigate to: App Service → minimalwave-blog
3. Left menu: Settings → "Configuration"
4. Application settings tab → "New application setting"
5. Add TWO settings:
   - **Name**: `AZURE_STORAGE_ACCOUNT_NAME`
   - **Value**: `minimalwavestorage`

   - **Name**: `AZURE_STORAGE_ACCOUNT_KEY`
   - **Value**: `<paste-key-from-step-3>`
6. Click "Save" → "Continue" (will restart app)

**Option B: Azure CLI** (if CLI works for you)
```bash
az webapp config appsettings set \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg \
  --settings \
    AZURE_STORAGE_ACCOUNT_NAME=minimalwavestorage \
    AZURE_STORAGE_ACCOUNT_KEY="<your-key>"
```

---

## Deployment Process

### 1. Final Code Review
```bash
# Check all changes
git status

# Review modified files
git diff
```

### 2. Apply Database Migrations
The migrations are already created. When you deploy, they'll run automatically via the Docker entrypoint script.

Migrations will add:
- `blog.Entry.image` (ImageField)
- `blog.Entry.image_alt` (CharField)
- `blog.Blogmark.image` (ImageField)
- `blog.Blogmark.image_alt` (CharField)
- `til.TIL.image` (ImageField)
- `til.TIL.image_alt` (CharField)

### 3. Commit and Deploy
```bash
# Stage all changes
git add .

# Commit
git commit -m "Add Azure Blob Storage for media files

- Add django-storages[azure] dependency
- Configure production.py for Azure Blob Storage
- Add image fields to Entry, Blogmark, and TIL models
- Create database migrations
- Update documentation

Ready for production deployment"

# Push to trigger deployment
git push origin main
```

### 4. Monitor Deployment
1. Watch GitHub Actions: https://github.com/YOUR_USERNAME/minimalwave-blog/actions
2. Wait for "Build and Deploy to Azure" workflow to complete (~5 minutes)
3. Check for success ✓

---

## Post-Deployment Verification

### Test Image Upload
1. Go to: https://jamesfishwick.com/admin/
2. Login with your admin credentials
3. Create new "Entry":
   - Fill in title, summary, body
   - Click "Choose File" in Image field
   - Upload a test image (JPG/PNG)
   - Add alt text: "Test image for deployment verification"
   - Save

### Verify Azure Storage
1. Go to Azure Portal → Storage Account: `minimalwavestorage`
2. Left menu: Containers → `media`
3. You should see: `blog/images/2025/10/your-image.jpg`

### Verify Image Display
1. Go to your blog post: https://jamesfishwick.com/2025/oct/<day>/<slug>/
2. Image should display from Azure CDN URL:
   `https://minimalwavestorage.blob.core.windows.net/media/blog/images/2025/10/your-image.jpg`

---

## How to Use Images in Posts

### Upload via Admin
1. Admin → Entries/Blogmarks/TILs
2. Image field: Choose File
3. Image alt: Add accessibility text
4. Save

### Embed in Markdown
After upload, the image path is shown in admin (e.g., `blog/images/2025/10/photo.jpg`)

**In your markdown body field:**
```markdown
# My Post Title

Here's some content. Now let me show you an image:

![Description for screen readers](/media/blog/images/2025/10/photo.jpg)

Continue with more content...
```

**OR use the Azure URL directly:**
```markdown
![Alt text](https://minimalwavestorage.blob.core.windows.net/media/blog/images/2025/10/photo.jpg)
```

### Image Optimization
Images are automatically optimized on upload:
- Resized to max 1200px width
- Quality set to 85%
- Maintains aspect ratio
- Converts RGBA to RGB for JPEGs

---

## Troubleshooting

### Images Not Uploading
**Check**: Azure App Service environment variables
```bash
az webapp config appsettings list \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg \
  --query "[?name=='AZURE_STORAGE_ACCOUNT_NAME' || name=='AZURE_STORAGE_ACCOUNT_KEY']"
```

### Images Not Displaying
**Check**: Container access permissions
- Go to Storage Account → Containers → media
- Access level should be "Private"
- Django handles signed URLs automatically

### Wrong URL in Production
**Check**: `production.py` configuration
- Verify `AZURE_ACCOUNT_NAME` and `AZURE_ACCOUNT_KEY` are set
- Check logs: `az webapp log tail --name minimalwave-blog --resource-group minimalwave-blog-rg`

---

## Cost Management

### Current Setup
- **Storage**: ~$0.018/GB/month
- **Transactions**: ~$0.004/10,000 operations
- **Egress**: First 100 GB/month free, then ~$0.087/GB

### Expected Monthly Cost
For typical blog with 50 images (~50MB):
- Storage: < $0.01/month
- Transactions: < $0.01/month
- Egress: Free (under 100 GB)
- **Total**: ~$0.02/month

### Monitor Usage
```bash
# Check storage usage
az storage account show-usage \
  --account-name minimalwavestorage \
  --query "value[0].currentValue"
```

---

## Rollback Plan

If deployment fails:

### 1. Revert Code
```bash
git revert HEAD
git push origin main
```

### 2. Remove Azure Config (Optional)
```bash
az webapp config appsettings delete \
  --name minimalwave-blog \
  --resource-group minimalwave-blog-rg \
  --setting-names AZURE_STORAGE_ACCOUNT_NAME AZURE_STORAGE_ACCOUNT_KEY
```

### 3. Wait for Auto-Redeploy
GitHub Actions will automatically redeploy the reverted version.

---

## Future Enhancements

### Azure CDN Integration
For high-traffic scenarios:
```python
# production.py
AZURE_CDN_HOSTNAME = 'cdn.jamesfishwick.com'
if AZURE_CDN_HOSTNAME:
    MEDIA_URL = f'https://{AZURE_CDN_HOSTNAME}/{AZURE_CONTAINER}/'
```

### AI-Generated Alt Text
Add Claude API integration:
```python
def generate_alt_text(image_file):
    # Use Claude API to analyze image
    # Return suggested alt text
    pass
```

### Image Migration Script
Migrate existing local images:
```python
# scripts/migrate_media_to_azure.py
# Copy all files from local media/ to Azure Blob Storage
```

---

## Quick Reference

### Storage Account Details
- **Name**: `minimalwavestorage`
- **Container**: `media`
- **URL**: https://minimalwavestorage.blob.core.windows.net
- **Region**: East US
- **Resource Group**: minimalwave-blog-rg

### Environment Variables
- `AZURE_STORAGE_ACCOUNT_NAME=minimalwavestorage`
- `AZURE_STORAGE_ACCOUNT_KEY=<from-azure-portal>`

### Test Checklist
- [ ] Storage account created
- [ ] Media container created (private)
- [ ] Storage key copied
- [ ] .env updated locally
- [ ] Azure App Service env vars configured
- [ ] Code committed and pushed
- [ ] Deployment succeeded
- [ ] Test image uploaded
- [ ] Image appears in Azure Storage
- [ ] Image displays on blog post
- [ ] Image URL uses Azure CDN

---

**Ready to deploy tomorrow!** 🚀
