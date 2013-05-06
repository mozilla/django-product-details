from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from product_details import settings_defaults


def settings_fallback(key):
    """Grab user-defined settings, or fall back to default."""
    try:
        return getattr(settings, key)
    except (AttributeError, ImportError, ImproperlyConfigured):
        return getattr(settings_defaults, key)


class DictCache(dict):
    """Mimic the django cache object. Timeouts are ignored."""

    def set(self, key, data, timeout=None):
        self[key] = data

    def delete(self, key):
        try:
            del self[key]
        except KeyError:
            pass


def get_cache(name):
    if name is None:
        return DictCache()
    else:
        # import late to avoid django config exception
        from django.core.cache import get_cache as dj_get_cache
        return dj_get_cache(name)
