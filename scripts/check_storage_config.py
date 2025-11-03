#!/usr/bin/env python
"""
Diagnostic script to check Azure storage configuration.
Run this via Azure App Service SSH or console.
"""
import os
import sys

print("=" * 70)
print("Azure Storage Configuration Diagnostic")
print("=" * 70)
print()

# Check environment variables
print("1. Environment Variables:")
print(f"   AZURE_STORAGE_ACCOUNT_NAME: {os.getenv('AZURE_STORAGE_ACCOUNT_NAME', 'NOT SET')}")
print(f"   AZURE_STORAGE_ACCOUNT_KEY: {'SET' if os.getenv('AZURE_STORAGE_ACCOUNT_KEY') else 'NOT SET'}")
print(f"   DJANGO_SETTINGS_MODULE: {os.getenv('DJANGO_SETTINGS_MODULE', 'NOT SET')}")
print()

# Import Django settings
try:
    import django
    django.setup()
    from django.conf import settings

    print("2. Django Settings (after setup):")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT SET')}")
    print(f"   MEDIA_URL: {settings.MEDIA_URL}")
    print(f"   AZURE_ACCOUNT_NAME: {getattr(settings, 'AZURE_ACCOUNT_NAME', 'NOT SET')}")
    print(f"   AZURE_STORAGE_ACCOUNT_NAME: {getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', 'NOT SET')}")
    print(f"   AZURE_STORAGE_KEY: {'SET' if hasattr(settings, 'AZURE_STORAGE_KEY') else 'NOT SET'}")
    print(f"   AZURE_STORAGE_CONTAINER_NAME: {getattr(settings, 'AZURE_STORAGE_CONTAINER_NAME', 'NOT SET')}")
    print()

    # Test storage backend
    print("3. Storage Backend Test:")
    try:
        from django.core.files.storage import default_storage
        print(f"   Storage class: {default_storage.__class__.__name__}")
        print(f"   Storage module: {default_storage.__class__.__module__}")

        # Try to list files
        try:
            dirs, files = default_storage.listdir('')
            print(f"   Root directories: {len(dirs)}")
            print(f"   Root files: {len(files)}")
        except Exception as e:
            print(f"   ⚠️  Cannot list root: {e}")

    except Exception as e:
        print(f"   ❌ Storage backend error: {e}")
    print()

    # Check if azure-storage-blob is installed
    print("4. Dependencies:")
    try:
        import azure.storage.blob
        print(f"   ✅ azure-storage-blob installed: {azure.storage.blob.__version__}")
    except ImportError:
        print(f"   ❌ azure-storage-blob NOT installed")

    try:
        import storages
        print(f"   ✅ django-storages installed")
    except ImportError:
        print(f"   ❌ django-storages NOT installed")

except Exception as e:
    print(f"❌ Error loading Django: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
