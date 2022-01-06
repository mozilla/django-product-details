from django.core.management import call_command
from django.test.testcases import TestCase

import responses
from mock import patch
from nose.tools import eq_

from product_details.storage import ProductDetailsStorage


class MockStorage(ProductDetailsStorage):
    """In-memory mock storage for testing."""

    def __init__(self, *args, **kwargs):
        super(MockStorage, self).__init__(*args, **kwargs)
        self.documents = {}

    def last_modified(self, name):
        doc = self.documents.get(name)
        if doc:
            return doc["last_modified"]

        return None

    def content(self, name):
        doc = self.documents.get(name)
        if doc:
            return doc["content"]

        return None

    def update(self, name, content, last_modified):
        self.documents[name] = {"content": content, "last_modified": last_modified}
        self.delete_cache(name)


class UpdateProductDetailsTests(TestCase):
    def setUp(self):
        # Mock out storage to avoid filesystem writes.
        self.storage = MockStorage(json_dir="/fake")
        storage_patch = patch(
            "product_details.management.commands.update_product_details.STORAGE_CLASS",
            return_value=self.storage,
        )
        storage_patch.start()
        self.addCleanup(storage_patch.stop)

    @responses.activate
    def test_run(self):
        responses.add(
            responses.GET,
            "http://example.com",
            body='<a href="test.json">test.json</a>',
        )
        responses.add(responses.GET, "http://example.com/regions/", body="")
        responses.add(
            responses.GET,
            "http://example.com/test.json",
            body='{"foo": "bar"}',
            adding_headers={"Last-Modified": "Sat, 01 Jan 2000 00:00:00 GMT"},
        )

        with self.settings(PROD_DETAILS_URL="http://example.com/"):
            call_command("update_product_details")

        eq_(
            self.storage.documents["test.json"],
            {
                "content": '{"foo": "bar"}',
                "last_modified": "Sat, 01 Jan 2000 00:00:00 GMT",
            },
        )
