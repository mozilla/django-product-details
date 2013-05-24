import functools
import time

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from product_details import settings_defaults


def settings_fallback(key):
    """Grab user-defined settings, or fall back to default."""
    try:
        return getattr(settings, key)
    except (AttributeError, ImportError, ImproperlyConfigured):
        return getattr(settings_defaults, key)


def memoize_for(ttl=300):
    """Memoizing decorator that caches return values for `ttl` seconds.

    Set ttl to 0 to cache indefinitely.
    """

    def memoize(obj):
        # via http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
        cache = obj._cache = {}

        @functools.wraps(obj)
        def memoizer(*args, **kwargs):
            now = time.time()
            try:
                value, last_updated = cache[args]
                if ttl > 0 and now - last_updated > ttl:
                    raise AttributeError
            except (KeyError, AttributeError):
                value = obj(*args, **kwargs)
                cache[args] = (value, now)
            return value

        return memoizer

    return memoize
