"""
When this module is imported, we load all the .json files and insert them as
module attributes using locals().  It's a magical and wonderful process.
"""
import json
import logging
import os

# During `pip install`, we need this to pass even without Django present.
try:
    from django.conf import settings
except ImportError:
    settings = None

from . import settings_defaults


VERSION = (0, 4)
__version__ = '.'.join(map(str, VERSION))
__all__ = ['VERSION', '__version__', 'product_details']

log = logging.getLogger('product_details')
log.setLevel(logging.WARNING)


class ProductDetails(object):
    """
    Main product details class. Implements the JSON files' content as
    attributes, e.g.: product_details.firefox_version_history .
    """
    json_data = {}

    def __init__(self):
        """Load JSON files and keep them in memory."""

        json_dir = self._settings_fallback('PROD_DETAILS_DIR')

        for filename in os.listdir(json_dir):
            if filename.endswith('.json'):
                name = os.path.splitext(filename)[0]
                path = os.path.join(json_dir, filename)
                self.json_data[name] = json.load(open(path))

    def _settings_fallback(self, key):
        """Grab user-defined settings, or fall back to default."""
        try:
            return getattr(settings, key)
        except (AttributeError, ImportError):
            return getattr(settings_defaults, key)

    def __getattr__(self, key):
        """Catch-all for access to JSON files."""
        try:
            return self.json_data[key]
        except KeyError:
            log.warn('Requested product details file %s not found!' % key)
            return FakeDict()

product_details = ProductDetails()


class FakeDict(dict):
    """Fake dictionary that'll pretend to know every key."""
    def __getitem__(self, key):
        return None
