import logging
import os


# URL to clone product_details JSON files from.
# Include trailing slash.
PROD_DETAILS_URL = 'http://svn.mozilla.org/libs/product-details/json/'

# Target dir to drop JSON files into (must be writable)
PROD_DETAILS_DIR = os.path.join(os.path.dirname(__file__), 'json')

# Cache for 1 day by default
PROD_DETAILS_TTL = 60 * 60 * 24

# log level.
LOG_LEVEL = logging.WARNING
