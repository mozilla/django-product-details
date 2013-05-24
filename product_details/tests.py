from time import sleep

from mock import Mock
from nose.tools import eq_

from product_details.utils import memoize_for


def test_memoize_for():
    @memoize_for(0)
    def testing(name):
        return name

    # function still works (sanity check)
    eq_(testing('dude'), 'dude')
    eq_(testing('walter'), 'walter')


def test_memoize_for_memoizes():
    """Should actually memoize things"""
    append_things = Mock()

    @memoize_for(0)
    def testing(name):
        return append_things(name)

    for i in range(10):
        testing('the dude')

    append_things.assert_called_once_with('the dude')


def test_memoize_for_memoizes_for_ttl():
    """Should actually memoize things"""
    append_things = Mock()

    @memoize_for(0.1)
    def testing(name):
        return append_things(name)

    testing('the dude')
    testing('the dude')
    sleep(0.1)
    testing('the dude')
    testing('the dude')

    eq_(append_things.call_count, 2)
