import logging
import os


# URL to clone product_details JSON files from.
# Include trailing slash.
PROD_DETAILS_URL = 'http://svn.mozilla.org/libs/product-details/json/'

# Target dir to drop JSON files into (must be writable)
PROD_DETAILS_DIR = os.path.join(os.path.dirname(__file__), 'json')

# Whether to check the modification time of the json files and reload
# without needing to restart the server.
PROD_DETAILS_AUTO_RELOAD = False
PROD_DETAILS_AUTO_RELOAD_REGIONS = False
# When auto_reload is on, only check the mtime once per TTL.
PROD_DETAILS_AUTO_RELOAD_TTL = 600  # 10 minutes

# log level.
LOG_LEVEL = logging.INFO
