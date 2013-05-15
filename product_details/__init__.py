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

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from product_details import settings_defaults


class MissingJSONData(IOError):
    pass


__version__ = '0.6'
__all__ = ['__version__', 'product_details', 'version_compare']

log = logging.getLogger('product_details')
log.setLevel(logging.WARNING)


def settings_fallback(key):
    """Grab user-defined settings, or fall back to default."""
    try:
        return getattr(settings, key)
    except (AttributeError, ImportError, ImproperlyConfigured):
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
                self.json_data[name] = json.load(open(path))

    def __getattr__(self, key):
        """Catch-all for access to JSON files."""
        try:
            return self.json_data[key]
        except KeyError:
            log.warn('Requested product details file %s not found!' % key)
            return collections.defaultdict(lambda: None)

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
            if self.json_data.get(key):
                return self.json_data.get(key)
            if os.path.exists(path):
                with codecs.open(path, encoding='utf8') as fd:
                    self.json_data[key] = json.load(fd)
                    return self.json_data[key]

        raise MissingJSONData('Unable to load region data for %s or en-US' %
                              locale)


product_details = ProductDetails()
