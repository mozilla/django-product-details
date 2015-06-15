Mozilla Product Details for Django
==================================

|Travis| |PyPI|

**Mozilla Product Details** is a
`library <http://viewvc.svn.mozilla.org/vc/libs/product-details/README?view=markup>`__
containing information about the latest versions, localizations, etc. of
`Mozilla <http://www.mozilla.org>`__ products (most notably Firefox,
Firefox for mobile, and Thunderbird).

From the original `README
file <http://viewvc.svn.mozilla.org/vc/libs/product-details/README?view=markup>`__:

::

    This library holds information about the current builds of Firefox and
    Thunderbird that Mozilla ships including:

    - Latest version numbers for all builds
    - English and Native names for all languages we support

This is a `Django <http://www.djangoproject.com/>`__ app allowing this
data to be used in Django projects. A Django management command can be
used as a cron job or called manually to keep the data in sync with
Mozilla.

Why?
----

The `data source <http://svn.mozilla.org/libs/product-details/>`__ of
Mozilla Product Details is a PHP library kept on the Mozilla SVN server,
and was originally written so it could be included into PHP projects via
an `SVN external <http://svnbook.red-bean.com/en/1.0/ch07s03.html>`__. A
simple ``svn up`` would fetch the latest data when it became available.

In the meantime, the Product Details library received an additional JSON
feed, allowing non-PHP projects to consume the data. If, however, the
consumer is not kept in SVN like the library is, there is no easy way to
keep the data up to date.

For Django projects, this app solves that problem.

Getting Started
---------------

Installing
~~~~~~~~~~

Install this library using ``pip``:

::

    pip install django-mozilla-product-details

... or by downloading the ``product_details`` directory and dropping it
into your django project.

Add ``product_details`` to your ``INSTALLED_APPS`` to enable the
management commands.

Configuration
~~~~~~~~~~~~~

No configuration should be necessary. However, you can add and alter the
following settings to your ``settings.py`` file if you disagree with the
defaults:

-  ``PROD_DETAILS_URL`` defaults to the JSON directory on the Mozilla
   SVN server. If you have a secondary mirror at hand, or you want this
   tool to download completely unrelated JSON files from somewhere else,
   adjust this setting. Include a trailing slash.
-  ``PROD_DETAILS_DIR`` is the target directory for the JSON files. It
   needs to be writable by the user that'll execute the management
   command, and readable by the user running the Django project.
   Defaults to: ``.../install_dir_of_this_app/product_details/json/``

This app uses Django's cache framework to store the product data so that
the data can be updated on the site without requiring a server restart.
The following settings will allow you to control how this works.

-  ``PROD_DETAILS_CACHE_NAME`` defaults to the cache in your ``CACHES``
   setting called ``default`` (django provides an in-memory cache here
   by default). If you provide a name of a cache configured in the
   Django configuration ``CACHES``, it will use that cache to store the
   file data instead.
-  ``PROD_DETAILS_CACHE_TIMEOUT`` If set to an integer, it represents
   the number of seconds the cached data should be kept per file.
   Defaults to 12 hours.

Updating the feed
~~~~~~~~~~~~~~~~~

To update the data, execute this:

::

    ./manage.py update_product_details

You want to run this once manually after installing the app. To
periodically pull in new data, you can make this a cron job.

**Note:** Please be considerate of the server when adding a cron job.
The data does not change often enough to warrant an update every minute
or so. Most applications will run perfectly fine if you pull new data
once a day or even less frequently. When in doubt, contact the author of
this library.

Using the data
~~~~~~~~~~~~~~

To use the data, just import the library:

::

    from product_details import product_details

The library turns all imported JSON files automatically into Python
objects. The contents are perhaps best inspected using
`IPython <http://ipython.scipy.org/>`__.

Version Compare
---------------

Product details comes with an implementation of version comparison code
for Mozilla-style product versions. Use it like this:

::

    >>> from product_details.version_compare import Version
    >>> v1 = Version('4.0b10')
    >>> v2 = Version('4.0b10pre')
    >>> v1 < v2
    False

The second useful part of the version compare code is generating a list
of unique versions, sorted by their release date, like this:

::

    >>> from product_details import product_details
    >>> from product_details.version_compare import version_list
    >>> version_list(product_details.firefox_history_development_releases)
    ['3.6.4', '3.6.3', '3.6', '3.6b5', '3.6b4', '3.6b3', '3.6b2', ... ]

Caveats / Known Issues
----------------------

1. While the management task will not overwrite existing files if the
   server returns bogus data (i.e., an empty document or unparseable
   JSON data), this library will also *never delete* a JSON file that
   was completely removed from the server. This is unlikely to happen
   very often, though.
2. You don't want to ``import product_details`` in ``settings.py`` as
   that would cause an import loop (since product\_details itself
   imports ``django.conf.settings``). However, if you must, you can
   lazily wrap the import like this, mitigating the problem:

   ::

       from django.utils.functional import lazy

       MY_LANGUAGES = ('en-US', 'de')
       class LazyLangs(list):
           def __new__(self):
               from product_details import product_details
               return [(lang.lower(), product_details.languages[lang]['native'])
                       for lang in MY_LANGUAGES]
       LANGUAGES = lazy(LazyLangs, list)()

Development
-----------

Patches are welcome.

To run tests, install ``tox`` and run ``tox`` from the project root.
This will run the tests in Python 2.6 and 2.7. If you don't have both of
those available, install ``nose`` and ``Mock`` and run the tests in your
current Python version by running ``nosetests``.

.. |Travis| image:: https://img.shields.io/travis/mozilla/django-product-details.svg
   :target: https://travis-ci.org/mozilla/django-product-details/
.. |PyPI| image:: https://img.shields.io/pypi/v/django-mozilla-product-details.svg
   :target: https://pypi.python.org/pypi/django-mozilla-product-details

Change Log
----------

0.7.1 - 2015-06-15
~~~~~~~~~~~~~~~~~~

-  Do not cache a file miss.
-  Catch an attempt to parse a non-JSON or corrupt file.

0.7 - 2015-05-22
~~~~~~~~~~~~~~~~

-  Use the Django cache framework to store product data, allowing data to be
   updated without a server restart.
-  Add and update tests, setup tox for testing across Python and Django versions,
   and setup Travis for CI.

0.6 - 2015-05-08
~~~~~~~~~~~~~~~~

-  Initial PyPI release. Prior to this it was released and installed via github.
