import datetime

from django.conf import settings
from django.utils import timezone

from blog.models import SiteSettings


def common_context(request):
    """
    Context processor to add common variables to all templates
    """
    # Runs on every request. Never let a settings-row lookup failure (DB down,
    # pre-migrate, read replica) raise here and 500 every page — including the
    # error pages, which also render base.html. Degrade to safe defaults.
    try:
        site_settings = SiteSettings.get_settings()
        site_name = site_settings.site_title
        site_description = site_settings.site_description
    except Exception:
        site_name = getattr(settings, "SITE_NAME", "")
        site_description = getattr(settings, "SITE_DESCRIPTION", "")

    # Prefer a configured absolute URL so canonical/JSON-LD are not built from
    # the attacker-controllable Host header (cache-poisoning / canonical hijack).
    # Falls back to the request host when SITE_URL is unset.
    site_url = getattr(settings, "SITE_URL", "") or request.build_absolute_uri(
        "/"
    ).rstrip("/")

    return {
        "site_name": site_name,
        "site_description": site_description,
        "site_url": site_url,
        "current_year": settings.USE_TZ
        and timezone.now().year
        or datetime.datetime.now().year,
        "plausible_enabled": settings.PLAUSIBLE_ENABLED,
        "plausible_domain": settings.PLAUSIBLE_DOMAIN,
        "plausible_script_url": settings.PLAUSIBLE_SCRIPT_URL,
    }
