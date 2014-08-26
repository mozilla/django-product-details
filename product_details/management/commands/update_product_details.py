import httplib
import json
import logging
from optparse import make_option
import os
import re
import shutil
import tempfile
import urllib2
from urlparse import urljoin

from django.core.management.base import NoArgsCommand, CommandError

from product_details import product_details
from product_details.utils import settings_fallback


log = logging.getLogger('prod_details')
log.addHandler(logging.StreamHandler())
log.setLevel(settings_fallback('LOG_LEVEL'))


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

        super(Command, self).__init__(*args, **kwargs)

    def handle_noargs(self, **options):
        self.options = options

        # Should we be quiet?
        if self.options['quiet']:
            log.setLevel(logging.WARNING)

        # Determine last update timestamp and check if we need to update again.
        if self.options['force']:
            log.info('Product details update forced.')

        self.download_directory(self.PROD_DETAILS_URL, self.PROD_DETAILS_DIR)
        self.download_directory(urljoin(self.PROD_DETAILS_URL, 'regions/'),
                                os.path.join(self.PROD_DETAILS_DIR, 'regions/'))

        log.debug('Product Details update run complete.')

    def download_directory(self, src, dest):
        # Grab list of JSON files from server.
        log.debug('Grabbing list of JSON files from the server from %s' % src)
        if not os.path.exists(dest):
            os.makedirs(dest)

        json_files = self.get_file_list(src, dest)
        if not json_files:
            return

        # Grab all modified JSON files from server and replace them locally.
        had_errors = False
        for json_file in json_files:
            if not self.download_json_file(src, dest, json_file):
                had_errors = True

        if had_errors:
            log.warn('Update run had errors, not storing "last updated" '
                     'timestamp.')
        else:
            # Save Last-Modified timestamp to detect updates against next time.
            log.debug('Writing last-updated timestamp (%s).' % (
                self.last_mod_response))
            with open(os.path.join(dest, '.last_update'),
                      'w') as timestamp_file:
                timestamp_file.write(self.last_mod_response)

    def get_file_list(self, src, dest):
        """
        Get list of files to be updated from the server.

        If no files have been modified, returns an empty list.
        """
        # If not forced: Read last updated timestamp
        self.last_update_local = None
        headers = {}

        if not self.options['force']:
            try:
                self.last_update_local = open(os.path.join(dest, '.last_update')).read()
                headers = {'If-Modified-Since': self.last_update_local}
                log.debug('Found last update timestamp: %s' % (
                    self.last_update_local))
            except (IOError, ValueError):
                log.info('No last update timestamp found.')

        # Retrieve file list if modified since last update
        try:
            resp = urllib2.urlopen(urllib2.Request(src, headers=headers))
        except urllib2.URLError, e:
            if e.code == httplib.NOT_MODIFIED:
                log.info('Product Details were up to date.')
                return []
            else:
                raise CommandError('Could not retrieve file list: %s' % e)

        # Remember Last-Modified header.
        self.last_mod_response = resp.info()['Last-Modified']

        json_files = set(re.findall(r'href="([^"]+.json)"', resp.read()))
        return json_files

    def download_json_file(self, src, dest, json_file):
        """
        Downloads a JSON file off the server, checks its validity, then drops
        it into the target dir.

        Returns True on success, False otherwise.
        """
        log.info('Updating %s from server' % json_file)

        if not self.options['force']:
            headers = {'If-Modified-Since': self.last_update_local}
        else:
            headers = {}

        # Grab JSON data if modified
        try:
            resp = urllib2.urlopen(urllib2.Request(
                urljoin(src, json_file), headers=headers))
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
            parsed = json.loads(json_data)
        except ValueError:
            log.warn('Could not parse JSON data from %s. Skipping.' % (
                json_file))
            return False

        # Write JSON data to HD.
        log.debug('Writing new copy of %s to %s.' % (
            json_file, dest))
        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.write(urllib2.urlopen(
            urljoin(src, json_file)).read())
        tf.close()

        # lchmod is available on BSD-based Unixes only.
        if hasattr(os, 'lchmod'):
            os.lchmod(tf.name, 0644)
        else:
            os.chmod(tf.name, 0644)

        shutil.move(tf.name, os.path.join(dest, json_file))

        # clear cache for file
        filename = json_file.rstrip('.json')
        if src.endswith('regions/'):
            filename = 'regions/' + filename
        product_details.delete_cache(filename)

        return True
