import codecs
import json
import logging
import os
import os.path
import tempfile
import shutil
from datetime import datetime

from django.db import transaction
from django.utils.six import text_type
from product_details import settings_defaults
from product_details.utils import get_django_cache, settings_fallback


log = logging.getLogger('product_details')


class ProductDetailsStorage(object):
    _cache_key = 'prod-details:{0}'

    def __init__(self, cache_name=None, cache_timeout=None, **kwargs):
        self._cache_timeout = cache_timeout or settings_fallback('PROD_DETAILS_CACHE_TIMEOUT')
        cache_name = cache_name or settings_fallback('PROD_DETAILS_CACHE_NAME')
        self._cache = get_django_cache(cache_name)

    def _get_cache_key(self, name):
        return self._cache_key.format(name)

    def delete_cache(self, name):
        """Clears the cache for a specific file.

        :param name: str file name.
        """
        self._cache.delete(self._get_cache_key(name))

    def clear_cache(self):
        """Clears the entire cache.

        WARNING: Only use this if you have a separate cache for product-details.
        """
        self._cache.clear()

    def last_modified(self, name):
        """
        Return the last-modified value for the requested file name.
        """
        raise NotImplementedError()

    def last_modified_datetime(self, name):
        fmt = '%a, %d %b %Y %H:%M:%S %Z'
        try:
            return datetime.strptime(self.last_modified(name), fmt)
        except (ValueError, TypeError):
            # bad date string format or None
            return None

    def content(self, name):
        """
        Return the content of the requested file name.
        """
        raise NotImplementedError()

    def data(self, name):
        """
        Return the parsed JSON data of the requested file name.
        """
        cache_key = self._get_cache_key(name)
        data = self._cache.get(cache_key)
        if data is None:
            content = self.content(name)
            if content:
                try:
                    data = json.loads(content)
                except ValueError:
                    return None
                if data:
                    self._cache.set(cache_key, data, self._cache_timeout)

        return data

    def update(self, name, content, last_modified):
        """
        Update the information for the requested file name.
        """
        raise NotImplementedError()


class PDDatabaseStorage(ProductDetailsStorage):
    @staticmethod
    def file_object(name):
        from product_details.models import ProductDetailsFile

        try:
            return ProductDetailsFile.objects.get(name=name)
        except ProductDetailsFile.DoesNotExist:
            return None

    def last_modified(self, name):
        fo = self.file_object(name)
        if fo:
            return fo.last_modified

        return None

    def content(self, name):
        fo = self.file_object(name)
        if fo:
            return text_type(fo.content)

        return None

    @transaction.atomic
    def update(self, name, content, last_modified):
        from product_details.models import ProductDetailsFile

        fo = self.file_object(name)
        if not fo:
            fo = ProductDetailsFile(name=name, content=content,
                                    last_modified=last_modified)
        else:
            fo.content = content
            fo.last_modified = last_modified

        fo.save()
        self.delete_cache(name)


class PDFileStorage(ProductDetailsStorage):
    last_modified_dir_file_name = '.last_update'

    def __init__(self, json_dir=None, cache_name=None, cache_timeout=None):
        super(PDFileStorage, self).__init__(cache_name, cache_timeout)
        self.json_dir = json_dir or settings_fallback('PROD_DETAILS_DIR')

    def last_modified_file_name(self, name):
        if name == '/':
            fn = self.last_modified_dir_file_name
        elif name.endswith('/'):
            fn = name + self.last_modified_dir_file_name
        else:
            path, fn = os.path.split(name)
            fn = '.{0}.last_modified'.format(fn)
            fn = os.path.join(path, fn)
        return os.path.join(self.json_dir, fn)

    def last_modified(self, name):
        lm_fn = self.last_modified_file_name(name)
        if not os.path.exists(lm_fn):
            lm_fn = self.last_modified_file_name(os.path.dirname(name) + '/')

        try:
            with open(lm_fn) as lm_fo:
                return lm_fo.read()
        except (IOError, ValueError):
            return None

    def content(self, name):
        filename = os.path.join(self.json_dir, name)
        try:
            with codecs.open(filename, 'rb', encoding='utf8') as json_file:
                return text_type(json_file.read())
        except IOError:
            log.warn('Requested product details file %s not found!' % name)
        except ValueError:
            log.warn('Requested product details file %s is not JSON!' % name)

        return None

    def update(self, name, content, last_modified):
        # use '/' as name when updating the last_modified data for the dir
        if name == '/':
            name = ''

        filename = os.path.join(self.json_dir, name)
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if content:
            log.debug('Writing new copy of %s to %s.' % (
                name, self.json_dir))
            tf = tempfile.NamedTemporaryFile(delete=False)
            tf.write(content.encode('utf8'))
            tf.close()

            # lchmod is available on BSD-based Unixes only.
            if hasattr(os, 'lchmod'):
                os.lchmod(tf.name, 0o644)
            else:
                os.chmod(tf.name, 0o644)

            shutil.move(tf.name, filename)
            lm_fn = self.last_modified_file_name(name)
        else:
            # in this case `name` should be either empty string or "regions/"
            lm_fn = os.path.join(filename, self.last_modified_dir_file_name)

        with open(lm_fn, 'w') as lm_fo:
            lm_fo.write(last_modified)

    def all_json_files(self):
        json_files = []
        for root, dirs, files in os.walk(self.json_dir):
            root = os.path.relpath(root, self.json_dir)
            root = '' if root == '.' else root
            json_files.extend(os.path.join(root, f) for f in files if f.endswith('.json'))

        return json_files


def json_file_data_to_db(model):
    """Import JSON file data into the DB.

    This is a function to be used in a data migration.
    It's here mostly so that it can be imported and tested.
    """
    from product_details.models import ProductDetailsFile

    PDModel = model or ProductDetailsFile
    if PDModel.objects.exists():
        # nothing to do if there's already data
        return

    default_path = settings_defaults.PROD_DETAILS_DIR

    storage = PDFileStorage()
    files = storage.all_json_files()

    if not files:
        if storage.json_dir == default_path:
            # no files to load
            return

        storage = PDFileStorage(json_dir=default_path)
        files = storage.all_json_files()

    if not files:
        return

    pd_objects = [PDModel(name=fn, content=storage.content(fn),
                          last_modified=storage.last_modified(fn)) for fn in files]
    pd_objects.append(PDModel(name='/', last_modified=storage.last_modified('/')))
    pd_objects.append(PDModel(name='regions/', last_modified=storage.last_modified('regions/')))

    PDModel.objects.bulk_create(pd_objects)
