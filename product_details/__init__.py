import codecs
import datetime
import json
import logging
import os
from collections import defaultdict

from product_details.utils import get_django_cache, settings_fallback


class MissingJSONData(IOError):
    pass


__version__ = '0.7.1'
__all__ = ['__version__', 'product_details', 'version_compare']

log = logging.getLogger('product_details')
log.setLevel(settings_fallback('LOG_LEVEL'))


class ProductDetails(object):
    """
    Main product details class. Implements the JSON files' content as
    attributes, e.g.: product_details.firefox_version_history .
    """
    _cache_key = 'prod-details:{0}'

    def __init__(self, json_dir=None, cache_name=None, cache_timeout=None):
        self.json_dir = json_dir or settings_fallback('PROD_DETAILS_DIR')
        self.cache_timeout = cache_timeout or settings_fallback('PROD_DETAILS_CACHE_TIMEOUT')
        cache_name = cache_name or settings_fallback('PROD_DETAILS_CACHE_NAME')
        self._cache = get_django_cache(cache_name)

    def __getattr__(self, key):
        return self._get_json_data(key)

    def _get_cache_key(self, key):
        return self._cache_key.format(key)

    def _get_json_file_data(self, key):
        filename = os.path.join(self.json_dir, key + '.json')
        try:
            with codecs.open(filename, encoding='utf8') as json_file:
                data = json.load(json_file)
        except IOError:
            log.warn('Requested product details file %s not found!' % key)
            return None
        except ValueError:
            log.warn('Requested product details file %s is not JSON!' % key)
            return None

        return data

    def _get_json_data(self, key):
        """Catch-all for access to JSON files."""
        cache_key = self._get_cache_key(key)
        data = self._cache.get(cache_key)
        if data is None:
            data = self._get_json_file_data(key)
            if data is not None:
                self._cache.set(cache_key, data, self.cache_timeout)

        return data or defaultdict(lambda: None)

    def delete_cache(self, key):
        """Clears the cache for a specific file.

        :param key: str file name with '.json' stripped off.
        """
        self._cache.delete(self._get_cache_key(key))

    def clear_cache(self):
        """Clears the entire cache.

        WARNING: Only use this if you have a separate cache for product-details.
        """
        self._cache.clear()

    @property
    def last_update(self):
        """Return the last-updated date, if it exists."""

        fmt = '%a, %d %b %Y %H:%M:%S %Z'
        dates = []
        for directory in (self.json_dir, os.path.join(self.json_dir, 'regions')):
            file = os.path.join(directory, '.last_update')
            try:
                with open(file) as f:
                    d = f.read()
            except IOError:
                d = ''

            try:
                dates.append(datetime.datetime.strptime(d, fmt))
            except ValueError:
                dates.append(None)

        if None in dates:
            return None
        # For backwards compat., just return the date of the parent.
        return dates[0]

    def get_regions(self, locale):
        """Loads regions json file into memory, but only as needed."""
        lookup = [locale, 'en-US']
        if '-' in locale:
            fallback, _, _ = locale.partition('-')
            lookup.insert(1, fallback)
        for l in lookup:
            key = 'regions/%s' % l
            data = self._get_json_data(key)
            if data:
                return data

        raise MissingJSONData('Unable to load region data for %s or en-US' %
                              locale)


product_details = ProductDetails()
