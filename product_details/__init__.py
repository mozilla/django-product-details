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

# During `pip install`, we need this to pass even without Django present.
try:
    from django.conf import settings
except ImportError:
    settings = None

from product_details import settings_defaults


VERSION = (0, 5)
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
        file = os.path.join(json_dir, '.last_update')
        try:
            with open(file) as f:
                d = f.read()
        except IOError:
            d = ''

        try:
            date = datetime.datetime.strptime(d, '%a, %d %b %Y %H:%M:%S %Z')
        except ValueError:
            date = None

        return date

    def get_regions(self, locale):
        """
        Get a list of region names for a specific locale as a
        dictionary with country codes as keys and localized names as
        values.
        """
        def json_file(name):
            return os.path.join(settings_fallback('PROD_DETAILS_DIR'),
                                'regions', '%s.json' % name)

        filepath = json_file(locale)

        if not os.path.exists(filepath):
            filepath = json_file('en-US')
            if not os.path.exists(filepath):
                raise Exception('Unable to load region data')

        with codecs.open(filepath, encoding='utf8') as fd:
            return json.load(fd)

product_details = ProductDetails()
