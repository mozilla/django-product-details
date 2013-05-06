from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from product_details import settings_defaults


def settings_fallback(key):
    """Grab user-defined settings, or fall back to default."""
    try:
        return getattr(settings, key)
    except (AttributeError, ImportError, ImproperlyConfigured):
        return getattr(settings_defaults, key)


def get_django_cache(cache_name):
    try:
        from django.core.cache import caches  # django 1.7+
        return caches[cache_name]
    except ImportError:
        from django.core.cache import get_cache
        return get_cache(cache_name)
    except ImproperlyConfigured:
        # dance to get around not-setup-django at import time
        return {}
