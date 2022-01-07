"""
Most of the version_compare tests are directly migrated from mozilla-central's reference
implementation.
"""
import json
from collections import defaultdict
from tempfile import mkdtemp

from datetime import datetime
from mock import Mock, patch, call
from nose.tools import eq_, ok_
from django.test.testcases import TestCase

import product_details
from product_details import settings_defaults
from product_details import storage
from product_details.models import ProductDetailsFile


class PDStorageClassMixin(object):
    storage = None

    def setUp(self):
        self.storage.clear_cache()

    def test_cache(self):
        good_data = {
            "the_dude.json": {"dude": "abiding"},
            "dammit_walter.json": {"walter": "finishing his coffee"},
        }
        with patch.object(
            self.storage, "dir_data", return_value=good_data
        ) as content_mock:
            eq_(self.storage.data("the_dude.json"), good_data["the_dude.json"])
            eq_(self.storage.data("the_dude.json"), good_data["the_dude.json"])
            eq_(
                self.storage.data("dammit_walter.json"), good_data["dammit_walter.json"]
            )
            eq_(
                self.storage.data("dammit_walter.json"), good_data["dammit_walter.json"]
            )
            content_mock.assert_called_once_with("versions")

    def test_cache_delete(self):
        good_data = {
            "the_dude.json": {"dude": "abiding"},
            "dammit_walter.json": {"walter": "finishing his coffee"},
        }
        with patch.object(
            self.storage, "dir_data", return_value=good_data
        ) as content_mock:
            eq_(self.storage.data("the_dude.json"), good_data["the_dude.json"])
            eq_(self.storage.data("the_dude.json"), good_data["the_dude.json"])
            eq_(
                self.storage.data("dammit_walter.json"), good_data["dammit_walter.json"]
            )
            self.storage.delete_cache("versions")
            eq_(self.storage.data("the_dude.json"), good_data["the_dude.json"])
            eq_(self.storage.data("the_dude.json"), good_data["the_dude.json"])
            eq_(
                self.storage.data("dammit_walter.json"), good_data["dammit_walter.json"]
            )
            content_mock.assert_called_with("versions")
            eq_(content_mock.call_count, 2)

    def test_no_cache_empty_data(self):
        """Empty data should not be cached."""
        with patch.object(self.storage, "dir_data", return_value={}) as content_mock:
            ok_(self.storage.data("the_dude.json") is None)
            ok_(self.storage.data("the_dude.json") is None)
            eq_(content_mock.call_count, 2)

    def test_update_file(self):
        self.storage.update("dude.json", "abide", "never modified")
        eq_(self.storage.content("dude.json"), "abide")
        eq_(self.storage.last_modified("dude.json"), "never modified")

        self.storage.update("dude.json", "bowling", "just now")
        eq_(self.storage.content("dude.json"), "bowling")
        eq_(self.storage.last_modified("dude.json"), "just now")

    def test_last_modified_datetime(self):
        self.storage.update("dude.json", "abide", "Sat, 10 Oct 2015 10:26:20 GMT")
        eq_(
            self.storage.last_modified_datetime("dude.json"),
            datetime(2015, 10, 10, 10, 26, 20),
        )

        self.storage.update("dude.json", "abide", "nihilists")
        ok_(self.storage.last_modified_datetime("dude.json") is None)

        with patch.object(self.storage, "last_modified") as lm_mock:
            lm_mock.return_value = None
            ok_(self.storage.last_modified_datetime("dude.json") is None)

    def test_store_dir_dates(self):
        self.storage.update("/", "", "just now")
        eq_(self.storage.last_modified("/"), "just now")

        self.storage.update("regions/", "", "a while back")
        eq_(self.storage.last_modified("regions/"), "a while back")

    def test_json_parsing(self):
        data = {"tried": "pacifism", "when": "not in nam"}
        self.storage.update("walter.json", json.dumps(data), "date")
        eq_(self.storage.data("walter.json"), data)

    def test_json_parsing_error(self):
        self.storage.update("donnie.json", "not json", "date")
        ok_(self.storage.data("donnie.json") is None)


class PDFileStorageTests(PDStorageClassMixin, TestCase):
    storage = storage.PDFileStorage(json_dir=mkdtemp())

    def test_last_modified_file_name(self):
        ok_(
            self.storage.last_modified_file_name("/").endswith(
                self.storage.last_modified_dir_file_name
            )
        )
        ok_(
            self.storage.last_modified_file_name("regions/").endswith(
                "regions/" + self.storage.last_modified_dir_file_name
            )
        )
        ok_(
            self.storage.last_modified_file_name("maude.json").endswith(
                ".maude.json.last_modified"
            )
        )
        ok_(
            self.storage.last_modified_file_name("regions/de.json").endswith(
                "regions/.de.json.last_modified"
            )
        )

    @patch("os.path.exists")
    @patch("product_details.storage.open", create=True)
    def test_last_modified_falls_back(self, open_mock, exists_mock):
        exists_mock.return_value = False
        open_mock.side_effect = IOError
        with patch.object(self.storage, "last_modified_file_name") as lmfn_mock:
            self.storage.last_modified("uli.json")
            self.storage.last_modified("publishers/treehorn.json")

        lmfn_mock.assert_has_calls(
            [
                call("uli.json"),
                call("/"),
                call("publishers/treehorn.json"),
                call("publishers/"),
            ]
        )

    def test_all_json_files(self):
        sto = storage.PDFileStorage(json_dir="/path/to/json/files")
        walk_results = [
            ("/path/to/json/files", ["regions"], ["dude.json", "walter.json"]),
            ("/path/to/json/files/regions", [], ["de.json", "fr.json"]),
        ]
        good_files = {"dude.json", "walter.json", "regions/de.json", "regions/fr.json"}
        with patch("os.walk", return_value=walk_results):
            jfiles = sto.all_json_files()

        eq_(set(jfiles), good_files)

    def test_all_json_files_bad_dir(self):
        sto = storage.PDFileStorage(json_dir="/does/not/exist")
        eq_(sto.all_json_files(), [])

    @patch("json.loads")
    def test_no_cache_corrupt_files(self, load_mock):
        """The fact that a file doesn't parse correctly should not be cached."""
        load_mock.side_effect = ValueError
        with patch.object(
            self.storage, "all_json_files", return_value=["the_dude.json"]
        ):
            with patch.object(self.storage, "content", return_value="dude"):
                ok_(self.storage.data("the_dude.json") is None)
                ok_(self.storage.data("the_dude.json") is None)
                eq_(load_mock.call_count, 2)

    def test_load_correct_files_per_folder(self):
        with patch.object(
            self.storage,
            "all_json_files",
            return_value=[
                "the_dude.json",
                "walter.json",
                "regions/es-MX.json",
                "regions/de.json",
            ],
        ):
            with patch.object(self.storage, "content", return_value='["dude"]'):
                versions_data = self.storage.dir_data("versions")
                regions_data = self.storage.dir_data("regions")
                self.assertNotIn("the_dude.json", regions_data)
                self.assertIn("the_dude.json", versions_data)
                self.assertNotIn("regions/es-MX.json", versions_data)
                self.assertIn("regions/es-MX.json", regions_data)
                self.assertEqual(len(versions_data), 2)
                self.assertEqual(len(regions_data), 2)


class PDDatabaseStorageTests(PDStorageClassMixin, TestCase):
    storage = storage.PDDatabaseStorage()

    def setUp(self):
        # delete the entries loaded by the migration
        ProductDetailsFile.objects.all().delete()
        super(PDDatabaseStorageTests, self).setUp()

    @patch("json.loads")
    def test_no_cache_corrupt_files(self, load_mock):
        """The fact that a file doesn't parse correctly should not be cached."""
        load_mock.side_effect = ValueError
        ProductDetailsFile.objects.create(name="the_dude.json", content="dude")
        ok_(self.storage.data("the_dude.json") is None)
        ok_(self.storage.data("the_dude.json") is None)
        eq_(load_mock.call_count, 2)

    def test_load_correct_files_per_folder(self):
        ProductDetailsFile.objects.create(name="the_dude.json", content='["dude"]')
        ProductDetailsFile.objects.create(name="walter.json", content='["walter"]')
        ProductDetailsFile.objects.create(
            name="regions/es-MX.json", content='["como no"]'
        )
        ProductDetailsFile.objects.create(name="regions/de.json", content='["bier"]')
        ProductDetailsFile.objects.create(name="regions/", content="")
        ProductDetailsFile.objects.create(name="/", content="")
        versions_data = self.storage.dir_data("versions")
        regions_data = self.storage.dir_data("regions")
        self.assertNotIn("the_dude.json", regions_data)
        self.assertIn("the_dude.json", versions_data)
        self.assertNotIn("regions/es-MX.json", versions_data)
        self.assertIn("regions/es-MX.json", regions_data)
        self.assertEqual(len(versions_data), 2)
        self.assertEqual(len(regions_data), 2)


@patch("product_details.product_details._real_storage", Mock())
class ProductDetailsTests(TestCase):
    pd = product_details.product_details

    def test_init(self):
        pddb = product_details.ProductDetails(
            storage_class="product_details.storage.PDDatabaseStorage"
        )
        ok_(isinstance(pddb._storage, storage.PDDatabaseStorage))
        pdfs = product_details.ProductDetails(
            storage_class="product_details.storage.PDFileStorage"
        )
        ok_(isinstance(pdfs._storage, storage.PDFileStorage))

    def test_file_requests(self):
        """Make sure it's asking for the right files."""
        good_data = {"dude": "abide"}
        self.pd._storage.data.return_value = good_data
        eq_(self.pd.get_regions("de"), good_data)
        self.pd._storage.data.assert_called_with("regions/de.json")
        self.pd._storage.reset_mock()
        eq_(self.pd.the_dude, good_data)
        self.pd._storage.data.assert_called_with("the_dude.json")

    def test_last_update(self):
        self.pd._storage.last_modified_datetime.return_value = "never"
        eq_(self.pd.last_update, "never")

    def test_no_file_response(self):
        self.pd._storage.data.return_value = None
        ok_(isinstance(self.pd.the_dude, defaultdict))
        with self.assertRaises(product_details.MissingJSONData):
            self.pd.get_regions("de")


class LoadJSONFileDataTests(TestCase):
    def test_db_has_data(self):
        model = Mock()
        model.objects.exists.return_value = True
        storage.json_file_data_to_db(model)
        self.assertFalse(model.objects.create.called)

    @patch.object(storage, "PDFileStorage")
    def test_attempts_load_from_default_if_bad_dir(self, file_storage_mock):
        """Should try to load JSON from default dir if the dir in settings does not exist."""
        model = Mock()
        model.objects.exists.return_value = False
        file_storage_mock.return_value.all_json_files.return_value = []
        file_storage_mock.return_value.json_dir = "/does/not/exist"
        storage.json_file_data_to_db(model)
        file_storage_mock.assert_called_with(
            json_dir=settings_defaults.PROD_DETAILS_DIR
        )
        eq_(file_storage_mock.call_count, 2)
        ok_(not model.objects.create.called)

    @patch.object(storage, "PDFileStorage")
    def test_loads_from_default_if_bad_dir(self, file_storage_mock):
        """Should try to load JSON from default dir if the dir in settings does not exist."""
        model = Mock()
        model.objects.exists.return_value = False
        storage_mock = file_storage_mock.return_value
        storage_mock.all_json_files.side_effect = [[], ["dude.json", "bunny.json"]]
        storage_mock.json_dir = "/does/not/exist"
        storage.json_file_data_to_db(model)
        file_storage_mock.assert_called_with(
            json_dir=settings_defaults.PROD_DETAILS_DIR
        )
        eq_(file_storage_mock.call_count, 2)
        model.assert_has_calls(
            [
                call(
                    name="dude.json",
                    content=storage_mock.content.return_value,
                    last_modified=storage_mock.last_modified.return_value,
                ),
                call(
                    name="bunny.json",
                    content=storage_mock.content.return_value,
                    last_modified=storage_mock.last_modified.return_value,
                ),
                call(name="/", last_modified=storage_mock.last_modified.return_value),
                call(
                    name="regions/",
                    last_modified=storage_mock.last_modified.return_value,
                ),
            ]
        )
        storage_mock.content.assert_has_calls([call("dude.json"), call("bunny.json")])
        storage_mock.last_modified.assert_has_calls(
            [call("dude.json"), call("bunny.json")]
        )

    @patch.object(storage, "PDFileStorage")
    def test_loads_from_settings_dir(self, file_storage_mock):
        """Should try to load JSON from default dir if the dir in settings does not exist."""
        model = Mock()
        model.objects.exists.return_value = False
        storage_mock = file_storage_mock.return_value
        storage_mock.all_json_files.return_value = ["walter.json", "donnie.json"]
        storage.json_file_data_to_db(model)
        file_storage_mock.assert_called_once_with()
        model.assert_has_calls(
            [
                call(
                    name="walter.json",
                    content=storage_mock.content.return_value,
                    last_modified=storage_mock.last_modified.return_value,
                ),
                call(
                    name="donnie.json",
                    content=storage_mock.content.return_value,
                    last_modified=storage_mock.last_modified.return_value,
                ),
                call(name="/", last_modified=storage_mock.last_modified.return_value),
                call(
                    name="regions/",
                    last_modified=storage_mock.last_modified.return_value,
                ),
            ]
        )
        storage_mock.content.assert_has_calls(
            [call("walter.json"), call("donnie.json")]
        )
        storage_mock.last_modified.assert_has_calls(
            [call("walter.json"), call("donnie.json")]
        )
