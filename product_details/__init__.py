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
from os.path import getmtime, splitext

from product_details.utils import memoize_for, settings_fallback


class MissingJSONData(IOError):
    pass


__version__ = '0.7'
__all__ = ['__version__', 'product_details', 'version_compare']

log = logging.getLogger('product_details')
log.setLevel(logging.WARNING)
DEFAULT_OPTIONS = {
    'json_dir': settings_fallback('PROD_DETAILS_DIR'),
    'auto_reload': settings_fallback('PROD_DETAILS_AUTO_RELOAD'),
    'auto_reload_regions': settings_fallback('PROD_DETAILS_AUTO_RELOAD_REGIONS'),
}


class ProductDetails(object):
    """
    Main product details class. Implements the JSON files' content as
    attributes, e.g.: product_details.firefox_version_history .
    """

    def __init__(self, **kwargs):
        """Load JSON files and keep them in memory.

        :param json_dir: ``str`` The directory in which to store the downloaded
                         JSON files.
        :param auto_reload: ``bool`` Whether to detect changes to JSON files
                            and reload them automatically.
        :param auto_reload_regions: ``bool`` Whether to detect changes to
                                    the region JSON files and reload
                                    them automatically.
        """
        self.json_data = {}
        self.json_mtime = {}
        self.options = DEFAULT_OPTIONS.copy()
        self.options.update(kwargs)

        # set options as properties
        for opt, val in self.options.items():
            setattr(self, opt, val)

        # pre-load product data
        for filename in os.listdir(self.json_dir):
            if filename.endswith('.json'):
                self._load_json_data(splitext(filename)[0])

    def _load_json_data(self, name):
        """Load data from a JSON file."""
        path = self._get_json_abspath(name)
        with codecs.open(path, encoding='utf8') as fd:
            self.json_data[name] = json.load(fd)
            if self.auto_reload:
                self.json_mtime[name] = getmtime(path)

    def _get_json_abspath(self, name):
        """Return the full path to the JSON file for given name."""
        return os.path.join(self.json_dir, '%s.json' % name)

    @memoize_for(settings_fallback('PROD_DETAILS_AUTO_RELOAD_TTL'))
    def _get_json_mtime(self, name):
        path = self._get_json_abspath(name)
        try:
            mtime = getmtime(path)
        except IOError:
            mtime = None

        return mtime

    def _auto_reload_json_data(self, name):
        mtime = self._get_json_mtime(name)
        if mtime and mtime > self.json_mtime.get(name):
            try:
                self._load_json_data(name)
            except IOError:
                pass

    def _get_json_data(self, name, auto_reload=False):
        """Accessor for JSON data."""
        if name in self.json_data:
            if auto_reload:
                self._auto_reload_json_data(name)

            return self.json_data[name]

        try:
            self._load_json_data(name)
        except IOError:
            pass

        try:
            return self.json_data[name]
        except KeyError:
            raise MissingJSONData('Requested product details '
                                  'file %s not found!' % name)

    def __getattr__(self, key):
        """Catch-all for access to JSON files."""
        try:
            return self._get_json_data(key, self.auto_reload)
        except MissingJSONData as e:
            log.warn(e.message)
            return collections.defaultdict(lambda: None)

    @property
    def last_update(self):
        """Return the last-updated date, if it exists."""

        json_dir = settings_fallback('PROD_DETAILS_DIR')
        fmt = '%a, %d %b %Y %H:%M:%S %Z'
        dates = []
        for directory in (json_dir, os.path.join(json_dir, 'regions')):
            lu_file = os.path.join(directory, '.last_update')
            try:
                with open(lu_file) as f:
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
        """Load regions json file into memory, but only as needed."""
        lookup = [locale, 'en-US']
        if '-' in locale:
            fallback, _, _ = locale.partition('-')
            lookup.insert(1, fallback)
        for l in lookup:
            key = 'regions/%s' % l
            try:
                return self._get_json_data(key, self.auto_reload_regions)
            except MissingJSONData:
                continue

        raise MissingJSONData('Unable to load region data for %s or en-US' %
                              locale)


product_details = ProductDetails()
