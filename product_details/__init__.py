"""
When this module is imported, we load all the .json files and insert them as
module attributes using locals().  It's a magical and wonderful process.
"""
import codecs
import collections
import datetime
import json
import logging
import os

from django.core.cache import cache

# During `pip install`, we need this to pass even without Django present.
try:
    from django.conf import settings
except ImportError:
    settings = None

from product_details import settings_defaults


VERSION = (0, 6)
__version__ = '.'.join(map(str, VERSION))
__all__ = ['VERSION', '__version__', 'product_details', 'version_compare']

log = logging.getLogger('product_details')
log.setLevel(logging.WARNING)


def settings_fallback(key):
    """Grab user-defined settings, or fall back to default."""
    try:
        return getattr(settings, key)
    except (AttributeError, ImportError):
        return getattr(settings_defaults, key)


class ProductDetails(object):
    """
    Main product details class. Implements the JSON files' content as
    attributes, e.g.: product_details.firefox_version_history .
    """
    json_data = {}

    def __init__(self):
        """Load JSON files and keep them in memory."""

        json_dir = settings_fallback('PROD_DETAILS_DIR')

        for filename in os.listdir(json_dir):
            if filename.endswith('.json'):
                name = os.path.splitext(filename)[0]
                path = os.path.join(json_dir, filename)
                self._set_data(name, json.load(open(path)))

    def __getattr__(self, key):
        """Catch-all for access to JSON files."""
        data = self._get_data(key)
        if data is None:
            log.warn('Requested product details file %s not found!' % key)
            data = collections.defaultdict(lambda: None)
        return data

    def _set_data(self, key, data):
        cache.set('product-details-%s' % key, data,
                  settings_fallback('PROD_DETAILS_TTL'))

    def _get_data(self, key, default=None):
        return cache.get('product-details-%s' % key) or None

    @property
    def last_update(self):
        """Return the last-updated date, if it exists."""

        json_dir = settings_fallback('PROD_DETAILS_DIR')
        fmt = '%a, %d %b %Y %H:%M:%S %Z'
        dates = []
        for directory in (json_dir, os.path.join(json_dir, 'regions')):
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
            path = os.path.join(settings_fallback('PROD_DETAILS_DIR'),
                                'regions', '%s.json' % l)
            if self._get_data(key):
                return self._get_data(key)
            if os.path.exists(path):
                with codecs.open(path, encoding='utf8') as fd:
                    self._set_data(key, json.load(fd))
                    return self._get_data(key)

        raise IOError('Unable to load region data for %s or en-US' % locale)


product_details = ProductDetails()
