import httplib
import json
import logging
from optparse import make_option
import re
import urllib2
from urlparse import urljoin

from django.core.management.base import NoArgsCommand, CommandError
from django.utils.module_loading import import_string

from product_details.utils import settings_fallback


log = logging.getLogger('prod_details')
log.addHandler(logging.StreamHandler())
log.setLevel(settings_fallback('LOG_LEVEL'))
STORAGE_CLASS = import_string(settings_fallback('PROD_DETAILS_STORAGE'))


class Command(NoArgsCommand):
    help = 'Update Mozilla product details off SVN.'
    requires_model_validation = False
    option_list = NoArgsCommand.option_list + (
        make_option('-f', '--force', action='store_true', dest='force',
                    default=False, help=(
                        'Download product details even if they have not been '
                        'updated since the last fetch.')),
        make_option('-q', '--quiet', action='store_true', dest='quiet',
                    default=False, help=(
                        'If no error occurs, swallow all output.')),
    )

    def __init__(self, *args, **kwargs):
        # some settings
        self.PROD_DETAILS_DIR = settings_fallback('PROD_DETAILS_DIR')
        self.PROD_DETAILS_URL = settings_fallback('PROD_DETAILS_URL')
        self._storage = STORAGE_CLASS(json_dir=self.PROD_DETAILS_DIR)

        super(Command, self).__init__(*args, **kwargs)

    def handle_noargs(self, **options):
        self.options = options

        # Should we be quiet?
        if self.options['quiet']:
            log.setLevel(logging.WARNING)

        # Determine last update timestamp and check if we need to update again.
        if self.options['force']:
            log.info('Product details update forced.')

        self.download_directory()
        self.download_directory('regions/')

        log.debug('Product Details update run complete.')

    def download_directory(self, dir=''):
        # Grab list of JSON files from server.
        src = urljoin(self.PROD_DETAILS_URL, dir)
        log.debug('Grabbing list of JSON files from the server from %s' % src)

        json_files = self.get_file_list(dir)
        if not json_files:
            return

        # Grab all modified JSON files from server and replace them locally.
        had_errors = False
        for json_file in json_files:
            if not self.download_json_file(urljoin(dir, json_file)):
                had_errors = True

        if had_errors:
            log.warn('Update run had errors, not storing "last updated" '
                     'timestamp.')
        else:
            # Save Last-Modified timestamp to detect updates against next time.
            log.debug('Writing last-updated timestamp (%s).' % (
                self.last_mod_response))
            self._storage.update(dir or '/', '', self.last_mod_response)

    def get_file_list(self, dir):
        """
        Get list of files to be updated from the server.

        If no files have been modified, returns an empty list.
        """
        # If not forced: Read last updated timestamp
        src = urljoin(self.PROD_DETAILS_URL, dir)
        self.last_update_local = None
        headers = {}

        if not self.options['force']:
            self.last_update_local = self._storage.last_modified(dir or '/')
            if self.last_update_local:
                headers = {'If-Modified-Since': self.last_update_local}
                log.debug('Found last update timestamp: %s' % (
                    self.last_update_local))
            else:
                log.info('No last update timestamp found.')

        # Retrieve file list if modified since last update
        try:
            resp = urllib2.urlopen(urllib2.Request(src, headers=headers))
        except urllib2.URLError, e:
            if e.code == httplib.NOT_MODIFIED:
                log.info('{} were up to date.'.format(
                    'Regions' if dir == 'regions/' else 'Product Details'))
                return []
            else:
                raise CommandError('Could not retrieve file list: %s' % e)

        # Remember Last-Modified header.
        self.last_mod_response = resp.info()['Last-Modified']

        json_files = set(re.findall(r'href="([^"]+.json)"', resp.read()))
        return json_files

    def download_json_file(self, json_file):
        """
        Downloads a JSON file off the server, checks its validity, then drops
        it into the target dir.

        Returns True on success, False otherwise.
        """
        log.info('Updating %s from server' % json_file)

        if not self.options['force']:
            headers = {'If-Modified-Since': self._storage.last_modified(json_file)}
        else:
            headers = {}

        # Grab JSON data if modified
        try:
            resp = urllib2.urlopen(urllib2.Request(
                urljoin(self.PROD_DETAILS_URL, json_file), headers=headers))
        except urllib2.URLError, e:
            if e.code == httplib.NOT_MODIFIED:
                log.debug('%s was not modified.' % json_file)
                return True
            else:
                log.warn('Error retrieving %s: %s' % (json_file, e))
                return False

        json_data = resp.read()

        # Empty results are fishy
        if not json_data:
            log.warn('JSON source for %s was empty. Cowardly denying to '
                     'import empty data.' % json_file)
            return False

        # Try parsing the file, import if it's valid JSON.
        try:
            json.loads(json_data)
        except ValueError:
            log.warn('Could not parse JSON data from %s. Skipping.' % json_file)
            return False

        # Write JSON data to HD.
        log.debug('Writing new copy of %s.' % json_file)
        self._storage.update(json_file, json_data, resp.info()['Last-Modified'])

        return True
