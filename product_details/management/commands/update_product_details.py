from datetime import datetime
import json
import logging
from optparse import make_option
import os
import re
import rfc822
import shutil
import tempfile
import time
import urllib2
from urlparse import urljoin

from django.conf import settings
from django.core.management.base import NoArgsCommand

from product_details import settings_defaults


log = logging.getLogger('reporter.prod_details')


class Command(NoArgsCommand):
    help = 'Update Mozilla product details off SVN.'
    option_list = NoArgsCommand.option_list + (
        make_option('--force', action='store_true', dest='force',
                    default=False, help=(
                        'Download product details even if they have not been '
                        'updated since the last fetch.')),
    )

    def __init__(self, *args, **kwargs):
        # some settings
        settings_fallback = lambda x: (
            getattr(settings, x, getattr(settings_defaults, x)))
        self.PROD_DETAILS_DIR = settings_fallback('PROD_DETAILS_DIR')
        self.PROD_DETAILS_URL = settings_fallback('PROD_DETAILS_URL')

        super(Command, self).__init__(*args, **kwargs)

    def handle_noargs(self, **options):
        # Determine last update timestamp and check if we need to update again.
        if options['force']:
            log.info('Product details update forced.')
        else:
            if self.is_current():
                return

        # Grab list of JSON files from server.
        log.debug('Grabbing list of JSON files from the server.')
        listing_response = urllib2.urlopen(self.PROD_DETAILS_URL)
        listing = listing_response.read()
        json_files = set(re.findall(r'href="([^"]+.json)"', listing))

        # Grab all JSON files from server and replace them locally.
        had_errors = False
        for json_file in json_files:
            if not self.download_json_file(json_file):
                had_errors = True

        if had_errors:
            log.warn('Update run had errors, not storing "last updated" '
                     'timestamp.')
        else:
            # Save Last-Modified timestamp to detect updates against next time.
            try:
                last_mod_header = (
                    listing_response.info()['Last-Modified'])
                update_timestamp = datetime.fromtimestamp(
                    time.mktime(rfc822.parsedate(last_mod_header)))
            except (IndexError, OverflowError, ValueError):
                log.warn('Last-Modified header not found for Product Details '
                         'source. Check server if this persists.')
            else:
                log.debug('Writing last-updated timestamp.')
                with open(os.path.join(self.PROD_DETAILS_DIR, '.last_update'),
                          'w') as timestamp_file:
                    timestamp_file.write(
                        str(time.mktime(update_timestamp.timetuple())))

        log.debug('Product Details update run complete.')

    def is_current(self):
        """
        Compare last local update timestamp with Last-Modified header of JSON
        source.

        returns True if up to date, False otherwise
        """
        try:
            with open(os.path.join(self.PROD_DETAILS_DIR, '.last_update'),
                      'r') as timestamp_file:
                last_update = datetime.fromtimestamp(
                    float(timestamp_file.read()))
            log.debug('Found last update timestamp: %s' % last_update)
        except (IOError, ValueError):
            log.info('No last update timestamp found.')
            return False
        else:
            # Issue HEAD request to check for Last-Modified header.
            resp = urllib2.urlopen(HeadRequest(self.PROD_DETAILS_URL))
            try:
                last_mod_header = resp.info()['Last-Modified']
                server_updated = datetime.fromtimestamp(
                    time.mktime(rfc822.parsedate(last_mod_header)))
            except (IndexError, OverflowError, ValueError):
                log.warn('Last-Modified header not found for Product Details '
                         'source. Check server if this persists.')
                return False
            else:
                if server_updated <= last_update:
                    log.info('Product Details were up to date.')
                    return True

    def download_json_file(self, json_file):
        """
        Downloads a JSON file off the server, checks its validity, then drops
        it into the target dir.

        Returns True on success, False otherwise.
        """
        log.debug('Updating %s from server' % json_file)
        tf = tempfile.NamedTemporaryFile(delete=False)
        json_data = urllib2.urlopen(
            urljoin(self.PROD_DETAILS_URL, json_file)).read()

        # Empty results are fishy
        if not json_data:
            log.warn('JSON source for %s was empty. Cowardly denying to '
                     'import empty data.' % json_file)
            return False

        # Try parsing the file, import if it's valid JSON.
        try:
            parsed = json.loads(json_data)
        except ValueError:
            log.warn('Could not parse JSON data from %s. Skipping.' % (
                json_file))
            return False

        # Write JSON data to HD.
        log.debug('Writing new copy of %s to %s.' % (
            json_file, self.PROD_DETAILS_DIR))
        tf.write(urllib2.urlopen(
            urljoin(self.PROD_DETAILS_URL, json_file)).read())
        tf.close()
        shutil.move(tf.name, os.path.join(self.PROD_DETAILS_DIR, json_file))

        return True


class HeadRequest(urllib2.Request):
    """HTTP HEAD request."""

    def get_method(self):
        return 'HEAD'
