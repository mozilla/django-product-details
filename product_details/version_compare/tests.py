"""
Most of these tests are directly migrated from mozilla-central's reference
implementation.
"""
from nose.tools import eq_

from product_details.version_compare import Version, version_list


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
    #"1.1.*",
    #"1.*",
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
  #"1.0+",
)


def test_version_compare():
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
