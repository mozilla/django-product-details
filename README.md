Mozilla Product Details for Django
==================================

*Mozilla Product Details* is a [library][readme] containing information about
the latest versions, localizations, etc. of Mozilla products (most notably
Firefox, Firefox for mobile, and Thunderbird).

This is a Django app allowing this data to be used in Django projects. A
Django management command can be used as a cron job or called manually
to keep the data in sync with Mozilla.

[readme]: http://viewvc.svn.mozilla.org/vc/libs/product-details/README?view=markup
[Mozilla]: http://www.mozilla.org
[Django]: http://www.djangoproject.com/

Why?
----
The [data source][viewvc] of Mozilla Product Details is a PHP library kept
on the Mozilla SVN server, and was originally written so it could be included
into PHP products via an [SVN external][SVNext]. A simple ``svn up`` would
fetch the latest data when it became available.

In the meantime, the Product Details library received an additional JSON feed,
allowing non-PHP projects to consume the data. If, however, the consumer is
not kept in SVN like the library is, there is no easy way to keep the data
up to date.

For Django projects, this app solved that problem.

[viewvc]: http://viewvc.svn.mozilla.org/vc/libs/product-details/
[SVNext]: http://svnbook.red-bean.com/en/1.0/ch07s03.html

Getting Started
---------------
### Installing
Install this library using ``easy_install`` or ``pip``, or by downloading
the ``product_details`` directory and dropping it into your django project.

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

*Note:* Please be considerate of the server when adding a cron job. The data
does not change often enough to warrant an update every minute or so. Most
applications will run perfectly fine if you pull new data once a day or even
less frequently. When in doubt, contact the author of this library.

### Using the data
To use the data, just import the library:

    import product_details

The library turns all imported JSON files automatically into Python objects.
The contents are perhaps best inspected using [IPython][ipython].

[ipython]: http://ipython.scipy.org/

Caveats / Known Issues
----------------------
While the management task will not overwrite existing files if the server
returns bogus data (i.e., an empty document or unparseable JSON data), this
library will also never delete a JSON file that was completely removed from
the server. This is unlikely to happen very often, though.

License
-------
This software is licensed under the [Mozilla Tri-License][MPL]:

    ***** BEGIN LICENSE BLOCK *****
    Version: MPL 1.1/GPL 2.0/LGPL 2.1

    The contents of this file are subject to the Mozilla Public License Version
    1.1 (the "License"); you may not use this file except in compliance with
    the License. You may obtain a copy of the License at
    http://www.mozilla.org/MPL/

    Software distributed under the License is distributed on an "AS IS" basis,
    WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
    for the specific language governing rights and limitations under the
    License.

    The Original Code is Mozilla Product Details.

    The Initial Developer of the Original Code is Mozilla.
    Portions created by the Initial Developer are Copyright (C) 2010
    the Initial Developer. All Rights Reserved.

    Contributor(s):
      Frederic Wenzel <fwenzel@mozilla.com> (Original Author)

    Alternatively, the contents of this file may be used under the terms of
    either the GNU General Public License Version 2 or later (the "GPL"), or
    the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
    in which case the provisions of the GPL or the LGPL are applicable instead
    of those above. If you wish to allow use of your version of this file only
    under the terms of either the GPL or the LGPL, and not to allow others to
    use your version of this file under the terms of the MPL, indicate your
    decision by deleting the provisions above and replace them with the notice
    and other provisions required by the GPL or the LGPL. If you do not delete
    the provisions above, a recipient may use your version of this file under
    the terms of any one of the MPL, the GPL or the LGPL.

    ***** END LICENSE BLOCK *****

[MPL]: http://www.mozilla.org/MPL/
