Mozilla Product Details for Django
==================================

**Mozilla Product Details** is a [library][readme] containing information about
the latest versions, localizations, etc. of [Mozilla][Mozilla] products (most
notably Firefox, Firefox for mobile, and Thunderbird).

From the original [README file][readme]:

    This library holds information about the current builds of Firefox and
    Thunderbird that Mozilla ships including:

    - Latest version numbers for all builds
    - English and Native names for all languages we support

This is a [Django][Django] app allowing this data to be used in Django
projects. A Django management command can be used as a cron job or called
manually to keep the data in sync with Mozilla.

[viewvc]: http://viewvc.svn.mozilla.org/vc/libs/product-details/
[readme]: http://viewvc.svn.mozilla.org/vc/libs/product-details/README?view=markup
[Mozilla]: http://www.mozilla.org
[Django]: http://www.djangoproject.com/

Why?
----
The [data source][SVNsource] of Mozilla Product Details is a PHP library kept
on the Mozilla SVN server, and was originally written so it could be included
into PHP projects via an [SVN external][SVNext]. A simple ``svn up`` would
fetch the latest data when it became available.

In the meantime, the Product Details library received an additional JSON feed,
allowing non-PHP projects to consume the data. If, however, the consumer is
not kept in SVN like the library is, there is no easy way to keep the data
up to date.

For Django projects, this app solves that problem.

[SVNsource]: http://svn.mozilla.org/libs/product-details/
[SVNext]: http://svnbook.red-bean.com/en/1.0/ch07s03.html

Getting Started
---------------
### Installing
Install this library using ``pip``:

    pip install -e git://github.com/fwenzel/django-mozilla-product-details#egg=django-mozilla-product-details

... or by downloading the ``product_details`` directory and dropping it into
your django project.

Add ``product_details`` to your ``INSTALLED_APPS`` to enable the management
commands.

### Configuration
No configuration should be necessary. However, you can add and alter the
following settings to your ``settings.py`` file if you disagree with the
defaults:

* ``PROD_DETAILS_URL`` defaults to the JSON directory on the Mozilla SVN
  server. If you have a secondary mirror at hand, or you want this tool to
  download completely unrelated JSON files from somewhere else, adjust this
  setting. Include a trailing slash.
* ``PROD_DETAILS_DIR`` is the target directory for the JSON files. It needs to
  be writable by the user that'll execute the management command, and readable
  by the user running the Django project. Defaults to:
  ``.../install_dir_of_this_app/product_details/json/``

### Updating the feed
To update the data, execute this:

    ./manage.py update_product_details

You want to run this once manually after installing the app. To periodically
pull in new data, you can make this a cron job.

**Note:** Please be considerate of the server when adding a cron job. The data
does not change often enough to warrant an update every minute or so. Most
applications will run perfectly fine if you pull new data once a day or even
less frequently. When in doubt, contact the author of this library.

### Using the data
To use the data, just import the library:

    import product_details

The library turns all imported JSON files automatically into Python objects.
The contents are perhaps best inspected using [IPython][ipython].

It is discouraged to import the submodules directly like this:

    # don't do this:
    from product_details import firefox_versions, languages

as it causes caveat #2 (see below). Alternatively, you could wrap it into a
try/except block, or manually drop the JSON files into the target directory
for the first time only.

[ipython]: http://ipython.scipy.org/

Caveats / Known Issues
----------------------
1. While the management task will not overwrite existing files if the server
   returns bogus data (i.e., an empty document or unparseable JSON data), this
   library will also *never delete* a JSON file that was completely removed from
   the server. This is unlikely to happen very often, though.
2. If you import the feed somewhere, then remove the JSON files, running the
   management command will still try to *run all imports* and fail because it
   can't find the data. You'll need to comment out that import, run
   ``update_product_details``, then comment it back in.
3. You don't want to ``import product_details`` in ``settings.py`` as that
   would cause an import loop (since product\_details itself imports
   ``django.conf.settings``). However, if you must, you can lazily wrap the
   import like this, mitigating the problem:

    from django.utils.functional import lazy

    MY_LANGUAGES = ('en-US', 'de')
    class LazyLangs(list):
        def __new__(self):
            import product_details
            return [(lang.lower(), product_details.languages[lang]['native'])
                    for lang in MY_LANGUAGES]
    LANGUAGES = lazy(LazyLangs, list)()
