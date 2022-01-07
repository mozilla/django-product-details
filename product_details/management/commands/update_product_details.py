import logging
import re
from urllib.parse import urljoin

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.module_loading import import_string


from product_details.utils import settings_fallback
from requests.exceptions import RequestException

log = logging.getLogger("prod_details")
log.addHandler(logging.StreamHandler())
log.setLevel(settings_fallback("LOG_LEVEL"))
STORAGE_CLASS = import_string(settings_fallback("PROD_DETAILS_STORAGE"))


class Command(BaseCommand):
    help = "Update Mozilla product details off SVN."
    requires_model_validation = False

    def __init__(self, *args, **kwargs):
        # some settings
        self.PROD_DETAILS_DIR = settings_fallback("PROD_DETAILS_DIR")
        self.PROD_DETAILS_URL = settings_fallback("PROD_DETAILS_URL")
        self._storage = STORAGE_CLASS(json_dir=self.PROD_DETAILS_DIR)
        self.is_db_storage = self._storage.storage_type == "db"

        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            dest="force",
            default=False,
            help=(
                "Download product details even if they have "
                "not been updated since the last fetch."
            ),
        )

        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            dest="quiet",
            default=False,
            help="If no error occurs, swallow all output.",
        ),
        parser.add_argument(
            "--database",
            default="default",
            help=(
                "Specifies the database to use, if using a db. "
                'Defaults to "default".'
            ),
        ),

    def handle(self, *args, **options):
        self.options = options

        # Should we be quiet?
        if options["quiet"]:
            log.setLevel(logging.WARNING)

        # Determine last update timestamp and check if we need to update again.
        if options["force"]:
            log.info("Product details update forced.")

        if self.is_db_storage:
            with transaction.atomic(using=options["database"]):
                self.download_directory()

            with transaction.atomic(using=options["database"]):
                self.download_directory("regions/")

        else:
            self.download_directory()
            self.download_directory("regions/")

        log.debug("Product Details update run complete.")

    def download_directory(self, dir=""):
        # Grab list of JSON files from server.
        src = urljoin(self.PROD_DETAILS_URL, dir)
        log.debug("Grabbing list of JSON files from the server from %s" % src)

        json_files = self.get_file_list(dir)
        if not json_files:
            return

        # Grab all modified JSON files from server and replace them locally.
        had_errors = False
        for json_file in json_files:
            if not self.download_json_file(urljoin(dir, json_file)):
                had_errors = True

        if had_errors:
            log.warn('Update run had errors, not storing "last updated" timestamp.')
        else:
            # Save Last-Modified timestamp to detect updates against next time.
            log.debug("Writing last-updated timestamp (%s)." % (self.last_mod_response))
            self._storage.update(dir or "/", "", self.last_mod_response)

    def get_file_list(self, dir):
        """
        Get list of files to be updated from the server.
        """
        src = urljoin(self.PROD_DETAILS_URL, dir)
        try:
            resp = requests.get(src)
        except RequestException as e:
            raise CommandError("Could not retrieve file list: %s" % e)

        # Remember Last-Modified header.
        self.last_mod_response = resp.headers.get("Last-Modified")

        json_files = set(re.findall(r'href="([^"]+.json)"', resp.text))
        return json_files

    def download_json_file(self, json_file):
        """
        Downloads a JSON file off the server, checks its validity, then drops
        it into the target dir.

        Returns True on success, False otherwise.
        """
        log.info("Updating %s from server" % json_file)

        if not self.options["force"]:
            headers = {"If-Modified-Since": self._storage.last_modified(json_file)}
        else:
            headers = {}

        # Grab JSON data if modified
        try:
            url = urljoin(self.PROD_DETAILS_URL, json_file)
            resp = requests.get(url, headers=headers)
        except RequestException as e:
            log.warn("Error retrieving %s: %s" % (json_file, e))
            return False

        if resp.status_code == requests.codes.not_modified:
            log.debug("%s was not modified." % json_file)
            return True

        # Empty results are fishy
        if not resp.text:
            log.warn(
                "JSON source for %s was empty. Cowardly denying to "
                "import empty data." % json_file
            )
            return False

        # Try parsing the file, import if it's valid JSON.
        try:
            resp.json()
        except ValueError:
            log.warn("Could not parse JSON data from %s. Skipping." % json_file)
            return False

        # Write JSON data to HD.
        log.debug("Writing new copy of %s." % json_file)
        self._storage.update(json_file, resp.text, resp.headers.get("Last-Modified"))

        return True
