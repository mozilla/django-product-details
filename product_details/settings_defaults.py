import logging
import os


# URL to clone product_details JSON files from.
# Include trailing slash.
PROD_DETAILS_URL = 'http://svn.mozilla.org/libs/product-details/json/'

# Target dir to drop JSON files into (must be writable)
PROD_DETAILS_DIR = os.path.join(os.path.dirname(__file__), 'json')

# log level.
LOG_LEVEL = logging.INFO

# name of cache to use
PROD_DETAILS_CACHE_NAME = 'default'  # django default

# how long to cache
PROD_DETAILS_CACHE_TIMEOUT = 60 * 60 * 12  # 12 hours

# data storage class
PROD_DETAILS_STORAGE = 'product_details.storage.PDFileStorage'
