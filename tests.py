from mock import Mock, patch
from nose.tools import eq_

import product_details
from product_details.utils import settings_fallback


def test_cache():
    pd = product_details.ProductDetails()
    good_data = {'dude': 'abiding'}
    pd._get_json_file_data = Mock(return_value=good_data)
    eq_(pd.the_dude, good_data)
    eq_(pd.the_dude, good_data)
    pd._get_json_file_data.assert_called_once_with('the_dude')

    # make sure the cache returns what was put in
    more_good_data = {'walter': 'finishing his coffee'}
    pd._get_json_file_data = Mock(return_value=more_good_data)
    eq_(pd.dammit_walter, more_good_data)
    eq_(pd.dammit_walter, more_good_data)
    pd._get_json_file_data.assert_called_once_with('dammit_walter')


def test_cache_delete():
    pd = product_details.ProductDetails()
    good_data = {'dude': 'abiding'}
    pd._get_json_file_data = Mock(return_value=good_data)
    eq_(pd.the_dude, good_data)
    eq_(pd.the_dude, good_data)
    pd.delete_cache('the_dude')
    eq_(pd.the_dude, good_data)
    eq_(pd.the_dude, good_data)
    pd._get_json_file_data.assert_called_with('the_dude')
    eq_(pd._get_json_file_data.call_count, 2)


def test_init():
    with patch.object(product_details, 'get_cache') as cache_mock:
        pd = product_details.ProductDetails()
    eq_(pd.json_dir, settings_fallback('PROD_DETAILS_DIR'))
    eq_(pd.cache_timeout, settings_fallback('PROD_DETAILS_CACHE_TIMEOUT'))
    cache_mock.assert_called_with(settings_fallback('PROD_DETAILS_CACHE_NAME'))

    with patch.object(product_details, 'get_cache') as cache_mock:
        pd = product_details.ProductDetails(json_dir='walter', cache_name='donny',
                                            cache_timeout=2)

    eq_(pd.json_dir, 'walter')
    eq_(pd.cache_timeout, 2)
    cache_mock.assert_called_with('donny')


def test_regions():
    """Make sure regions still work"""
    pd = product_details.ProductDetails()
    good_data = {'dude': 'abide'}
    pd._get_json_data = Mock(return_value=good_data)
    eq_(pd.get_regions('de'), good_data)
    pd._get_json_data.assert_called_with('regions/de')
