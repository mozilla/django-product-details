import copy

from django.test import SimpleTestCase

from nose.tools import eq_

from product_details.version_compare import (
    Version,
    version_dict,
    version_int,
    version_list,
)


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
    "100.1pre",
    "100.1pre1a",
    "100.1pre1",
    "100.1pre10a",
    "100.1pre10",
    "100.1",
    "100.1.0.1",
    "100.1.1",
    "101.0.1",
)

# Every version in this list means the same version number.
# TODO add support for + signs.
EQUALITY = (
    "1.1pre",
    "1.1pre0",
    # "1.0+",
)
EQUALITY_FF100 = (
    "101.1pre",
    "101.1pre0",
    # "1.0+",
)


class TestVersions(SimpleTestCase):
    def test_version_compare(self):
        """Test version comparison code, for parity with mozilla-central."""
        numlist = enumerate(map(lambda v: Version(v), COMPARISONS))
        for i, v1 in numlist:
            for j, v2 in numlist:
                if i < j:
                    assert v1 < v2, "%s is not less than %s" % (v1, v2)
                elif i > j:
                    assert v1 > v2, "%s is not greater than %s" % (v1, v2)
                else:
                    eq_(v1, v2)

        equal_vers = map(lambda v: Version(v), EQUALITY)
        for v1 in equal_vers:
            for v2 in equal_vers:
                eq_(v1, v2)
        equal_vers = map(lambda v: Version(v), EQUALITY_FF100)
        for v1 in equal_vers:
            for v2 in equal_vers:
                eq_(v1, v2)

    def test_simplify_version(self):
        """Make sure version simplification works."""
        versions = {
            "4.0b1": "4.0b1",
            "3.6": "3.6",
            "3.6.4b1": "3.6.4b1",
            "3.6.4build1": "3.6.4",
            "3.6.4build17": "3.6.4",
            "101.1": "101.1",
            "101.1b1": "101.1b1",
            "101.1.1b1": "101.1.1b1",
            "101.1.1build9": "101.1.1",
            "101.1alpha": "101.1",
        }
        for v in versions:
            ver = Version(v)
            eq_(ver.simplified, versions[v])

    def test_dict_vs_int(self):
        """
        version_dict and _int can use each other's data but must not overwrite
        it.
        """
        version_string = "4.0b8pre"
        dict1 = copy.copy(version_dict(version_string))
        int1 = version_int(version_string)
        dict2 = version_dict(version_string)
        int2 = version_int(version_string)
        eq_(dict1, dict2)
        eq_(int1, int2)

    def test_dict_vs_int_ff100(self):
        """
        version_dict and _int can use each other's data but must not overwrite
        it.
        """
        version_string = "104.0b8pre"
        dict1 = copy.copy(version_dict(version_string))
        int1 = version_int(version_string)
        dict2 = version_dict(version_string)
        int2 = version_int(version_string)
        eq_(dict1, dict2)
        eq_(int1, int2)

    def test_version_list(self):
        """Test if version lists are generated properly."""
        my_versions = {
            "4.0b2build8": "2010-12-06",
            "3.0": "2010-12-01",
            "4.0b1": "2010-11-24",
            "4.0b2build7": "2010-12-05",
            "100.0b1": "2022-05-01",
            "100.0b1build7": "2022-05-02",
        }
        expected = ("100.0b1", "4.0b2", "4.0b1")

        test_list = version_list(my_versions, hide_below="4.0b1")

        # Check if the generated version list is the same as we expect.
        eq_(len(expected), len(test_list))
        for n, v in enumerate(test_list):
            eq_(v, expected[n])
