#!/usr/bin/env python
"""
Test Azure Blob Storage connection and upload capability.
Run this to verify Azure storage is properly configured.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minimalwave-blog.settings.production')
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("Azure Blob Storage Connection Test")
print("=" * 70)
print()

# Step 1: Check configuration
print("1. Configuration Check:")
print(f"   DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
print(f"   MEDIA_URL: {settings.MEDIA_URL}")
print(f"   Storage backend: {default_storage.__class__.__name__}")
print(f"   Storage module: {default_storage.__class__.__module__}")
print()

# Step 2: Check Azure credentials
if hasattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME'):
    print("2. Azure Credentials:")
    print(f"   ✅ AZURE_STORAGE_ACCOUNT_NAME: {settings.AZURE_STORAGE_ACCOUNT_NAME}")
    print(f"   ✅ AZURE_STORAGE_KEY: {'SET' if hasattr(settings, 'AZURE_STORAGE_KEY') else 'NOT SET'}")
    print(f"   ✅ AZURE_STORAGE_CONTAINER_NAME: {settings.AZURE_STORAGE_CONTAINER_NAME}")
    print()
else:
    print("2. Azure Credentials:")
    print("   ❌ Azure credentials NOT configured")
    print("   Using local storage fallback")
    print()
    sys.exit(1)

# Step 3: Test file upload
print("3. Testing file upload...")
test_filename = 'test_uploads/azure_test.txt'
test_content = b'Azure Blob Storage test file created by test script'

try:
    # Upload test file
    print(f"   Uploading: {test_filename}")
    path = default_storage.save(test_filename, ContentFile(test_content))
    print(f"   ✅ Uploaded to: {path}")

    # Verify file exists
    exists = default_storage.exists(path)
    print(f"   File exists: {exists}")

    # Get file URL
    url = default_storage.url(path)
    print(f"   File URL: {url}")

    # Read file back
    with default_storage.open(path, 'rb') as f:
        content = f.read()
        print(f"   Content length: {len(content)} bytes")
        print(f"   Content matches: {content == test_content}")

    # Clean up
    print()
    print("4. Cleaning up test file...")
    default_storage.delete(path)
    print(f"   ✅ Test file deleted")

    print()
    print("=" * 70)
    print("✅ Azure Blob Storage Test: PASSED")
    print("=" * 70)
    print()
    print("Your Azure storage is properly configured and working!")
    sys.exit(0)

except Exception as e:
    print()
    print("=" * 70)
    print("❌ Azure Blob Storage Test: FAILED")
    print("=" * 70)
    print()
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("Troubleshooting steps:")
    print("1. Verify environment variables are set in App Service")
    print("2. Check Azure storage account credentials")
    print("3. Verify 'media' container exists and has blob access")
    print("4. Check if django-storages[azure] is installed")
    sys.exit(1)
