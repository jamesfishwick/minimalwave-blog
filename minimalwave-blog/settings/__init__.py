"""
Settings module initialization
"""
import os

# Default to development settings
DJANGO_SETTINGS_MODULE = os.environ.get('DJANGO_SETTINGS_MODULE', 'minimalwave-blog.settings.development')

if DJANGO_SETTINGS_MODULE == 'minimalwave-blog.settings.production':
    from .production import *
else:
    from .development import *
