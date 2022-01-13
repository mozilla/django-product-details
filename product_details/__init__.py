import logging
from collections import defaultdict

from django.utils.module_loading import import_string

from product_details.utils import settings_fallback


class MissingJSONData(IOError):
    pass


__version__ = "1.0.1"
__all__ = ["__version__", "product_details", "version_compare"]

log = logging.getLogger("product_details")
log.setLevel(settings_fallback("LOG_LEVEL"))


class ProductDetails(object):
    """
    Main product details class. Implements the JSON files' content as
    attributes, e.g.: product_details.firefox_version_history .
    """

    _cache_key = "prod-details:{0}"

    def __init__(
        self, json_dir=None, cache_name=None, cache_timeout=None, storage_class=None
    ):
        self._storage_class = import_string(
            storage_class or settings_fallback("PROD_DETAILS_STORAGE")
        )
        self._json_dir = json_dir
        self._cache_name = cache_name
        self._cache_timeout = cache_timeout
        self._real_storage = None

    @property
    def _storage(self):
        if not self._real_storage:
            self._real_storage = self._storage_class(
                cache_name=self._cache_name,
                cache_timeout=self._cache_timeout,
                json_dir=self._json_dir,
            )
        return self._real_storage

    def __getattr__(self, key):
        data = self._storage.data("{0}.json".format(key))
        return data or defaultdict(lambda: None)

    def delete_cache(self, key):
        """Clears the cache for a specific file.

        :param key: str file name with '.json' stripped off.
        """
        self._storage.delete_cache(self._get_cache_key(key))

    def clear_cache(self):
        """Clears the entire cache.

        WARNING: Only use this if you have a separate cache for product-details.
        """
        self._storage.clear_cache()

    @property
    def last_update(self):
        """Return the last-updated date, if it exists."""
        return self._storage.last_modified_datetime("/")

    def get_regions(self, locale):
        """Loads regions json file into memory, but only as needed."""
        lookup = [locale, "en-US"]
        if "-" in locale:
            fallback, _, _ = locale.partition("-")
            lookup.insert(1, fallback)
        for lk in lookup:
            key = "regions/%s.json" % lk
            data = self._storage.data(key)
            if data:
                return data

        raise MissingJSONData("Unable to load region data for %s or en-US" % locale)


product_details = ProductDetails()
