import datetime
from django.conf import settings
from django.utils import timezone
from blog.models import SiteSettings

def common_context(request):
    """
    Context processor to add common variables to all templates
    """
    site_settings = SiteSettings.get_settings()

    return {
        'site_name': site_settings.site_title,
        'site_description': site_settings.site_description,
        'site_url': request.build_absolute_uri('/').rstrip('/'),
        'current_year': settings.USE_TZ and timezone.now().year or datetime.datetime.now().year,
        'plausible_enabled': settings.PLAUSIBLE_ENABLED,
        'plausible_domain': settings.PLAUSIBLE_DOMAIN,
        'plausible_script_url': settings.PLAUSIBLE_SCRIPT_URL,
    }
