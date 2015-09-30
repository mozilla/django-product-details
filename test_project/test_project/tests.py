"""
Most of the version_compare tests are directly migrated from mozilla-central's reference
implementation.
"""
import copy
from collections import defaultdict
import json
from tempfile import mkdtemp

from mock import Mock, patch
from nose.tools import eq_, ok_

from django.test.testcases import TestCase

import product_details
from product_details import storage
from product_details.version_compare import (
    Version, version_list, version_dict, version_int)


# Versions to test listed in ascending order, none can be equal.
# TODO Add support for asterisks.
COMPARISONS = (
    "0.9",
    "0.9.1",
    "1.0pre1",
    "1.0pre2",
    "1.0",
    "1.1pre",
    "1.1pre1a",
    "1.1pre1",
    "1.1pre10a",
    "1.1pre10",
    "1.1",
    "1.1.0.1",
    "1.1.1",
    # "1.1.*",
    # "1.*",
    "2.0",
    "2.1",
    "3.0.-1",
    "3.0",
)

# Every version in this list means the same version number.
# TODO add support for + signs.
EQUALITY = (
    "1.1pre",
    "1.1pre0",
    # "1.0+",
)


# VERSION_COMPARE TESTS


def test_version_compare():
    """Test version comparison code, for parity with mozilla-central."""
    numlist = enumerate(map(lambda v: Version(v), COMPARISONS))
    for i, v1 in numlist:
        for j, v2 in numlist:
            if i < j:
                assert v1 < v2, '%s is not less than %s' % (v1, v2)
            elif i > j:
                assert v1 > v2, '%s is not greater than %s' % (v1, v2)
            else:
                eq_(v1, v2)

    equal_vers = map(lambda v: Version(v), EQUALITY)
    for v1 in equal_vers:
        for v2 in equal_vers:
            eq_(v1, v2)


def test_simplify_version():
    """Make sure version simplification works."""
    versions = {
        '4.0b1': '4.0b1',
        '3.6': '3.6',
        '3.6.4b1': '3.6.4b1',
        '3.6.4build1': '3.6.4',
        '3.6.4build17': '3.6.4',
    }
    for v in versions:
        ver = Version(v)
        eq_(ver.simplified, versions[v])


def test_dict_vs_int():
    """
    version_dict and _int can use each other's data but must not overwrite
    it.
    """
    version_string = '4.0b8pre'
    dict1 = copy.copy(version_dict(version_string))
    int1 = version_int(version_string)
    dict2 = version_dict(version_string)
    int2 = version_int(version_string)
    eq_(dict1, dict2)
    eq_(int1, int2)


def test_version_list():
    """Test if version lists are generated properly."""
    my_versions = {
        '4.0b2build8': '2010-12-06',
        '3.0': '2010-12-01',
        '4.0b1': '2010-11-24',
        '4.0b2build7': '2010-12-05',
    }
    expected = ('4.0b2', '4.0b1')

    test_list = version_list(my_versions, hide_below='4.0b1')

    # Check if the generated version list is the same as we expect.
    eq_(len(expected), len(test_list))
    for n, v in enumerate(test_list):
        eq_(v, expected[n])


# PRODUCT DETAILS TESTS

class PDStorageClassMixin(object):
    storage = None

    def setUp(self):
        self.storage.clear_cache()
    
    def test_cache(self):
        good_data = {'dude': 'abiding'}
        with patch.object(self.storage, 'content',
                          return_value=json.dumps(good_data)) as content_mock:
            eq_(self.storage.data('the_dude.json'), good_data)
            eq_(self.storage.data('the_dude.json'), good_data)
            content_mock.assert_called_once_with('the_dude.json')

        # make sure the cache returns what was put in
        good_data = {'walter': 'finishing his coffee'}
        with patch.object(self.storage, 'content',
                          return_value=json.dumps(good_data)) as content_mock:
            eq_(self.storage.data('dammit_walter.json'), good_data)
            eq_(self.storage.data('dammit_walter.json'), good_data)
            content_mock.assert_called_once_with('dammit_walter.json')

    def test_cache_delete(self):
        good_data = {'dude': 'abiding'}
        with patch.object(self.storage, 'content',
                          return_value=json.dumps(good_data)) as content_mock:
            eq_(self.storage.data('the_dude.json'), good_data)
            eq_(self.storage.data('the_dude.json'), good_data)
            eq_(self.storage.data('walter.json'), good_data)
            self.storage.delete_cache('the_dude.json')
            eq_(self.storage.data('the_dude.json'), good_data)
            eq_(self.storage.data('the_dude.json'), good_data)
            eq_(self.storage.data('walter.json'), good_data)
            content_mock.assert_called_with('the_dude.json')
            eq_(content_mock.call_count, 3)

    def test_no_cache_missing_files(self):
        """The fact that a file doesn't exist should not be cached."""
        with patch.object(self.storage, 'content',
                          return_value=None) as content_mock:
            ok_(self.storage.data('the_dude.json') is None)
            ok_(self.storage.data('the_dude.json') is None)
            eq_(content_mock.call_count, 2)

    @patch('json.loads')
    def test_no_cache_corrupt_files(self, load_mock):
        """The fact that a file doesn't parse correctly should not be cached."""
        load_mock.side_effect = ValueError
        with patch.object(self.storage, 'content',
                          return_value='["dude"]') as content_mock:
            ok_(self.storage.data('the_dude.json') is None)
            ok_(self.storage.data('the_dude.json') is None)
            eq_(content_mock.call_count, 2)

    def test_update_file(self):
        self.storage.update('dude.json', 'abide', 'never modified')
        eq_(self.storage.content('dude.json'), 'abide')
        eq_(self.storage.last_modified('dude.json'), 'never modified')

        self.storage.update('dude.json', 'bowling', 'just now')
        eq_(self.storage.content('dude.json'), 'bowling')
        eq_(self.storage.last_modified('dude.json'), 'just now')

    def test_store_dir_dates(self):
        self.storage.update('/', '', 'just now')
        eq_(self.storage.last_modified('/'), 'just now')

        self.storage.update('regions/', '', 'a while back')
        eq_(self.storage.last_modified('regions/'), 'a while back')

    def test_json_parsing(self):
        data = {'tried': 'pacifism', 'when': 'not in nam'}
        self.storage.update('walter.json', json.dumps(data), 'date')
        eq_(self.storage.data('walter.json'), data)

    def test_json_parsing_error(self):
        self.storage.update('donnie.json', 'not json', 'date')
        ok_(self.storage.data('donnie.json') is None)


class PDFileStorageTests(PDStorageClassMixin, TestCase):
    storage = storage.PDFileStorage(json_dir=mkdtemp())

    def test_last_modified_file_name(self):
        ok_(self.storage.last_modified_file_name('/').endswith(
            self.storage.last_modified_dir_file_name))
        ok_(self.storage.last_modified_file_name('regions/').endswith(
            'regions/' + self.storage.last_modified_dir_file_name))
        ok_(self.storage.last_modified_file_name('maude.json').endswith('.maude.json.last_modified'))
        ok_(self.storage.last_modified_file_name('regions/de.json').endswith(
            'regions/.de.json.last_modified'))


class PDDatabaseStorageTests(PDStorageClassMixin, TestCase):
    storage = storage.PDDatabaseStorage()


@patch('product_details.product_details._storage', Mock())
class ProductDetailsTests(TestCase):
    pd = product_details.product_details

    def test_init(self):
        pddb = product_details.ProductDetails(
            storage_class='product_details.storage.PDDatabaseStorage')
        ok_(isinstance(pddb._storage, storage.PDDatabaseStorage))
        pdfs = product_details.ProductDetails(
            storage_class='product_details.storage.PDFileStorage')
        ok_(isinstance(pdfs._storage, storage.PDFileStorage))

    def test_file_requests(self):
        """Make sure it's asking for the right files."""
        good_data = {'dude': 'abide'}
        self.pd._storage.data.return_value = good_data
        eq_(self.pd.get_regions('de'), good_data)
        self.pd._storage.data.assert_called_with('regions/de.json')
        self.pd._storage.reset_mock()
        eq_(self.pd.the_dude, good_data)
        self.pd._storage.data.assert_called_with('the_dude.json')

    def test_last_update(self):
        self.pd._storage.last_updated.return_value = 'never'
        eq_(self.pd.last_update, 'never')

    def test_no_file_response(self):
        self.pd._storage.data.return_value = None
        ok_(isinstance(self.pd.the_dude, defaultdict))
        with self.assertRaises(product_details.MissingJSONData):
            self.pd.get_regions('de')
