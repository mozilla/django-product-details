# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from product_details.storage import json_file_data_to_db


def load_json_file_data(apps, schema_editor):
    json_file_data_to_db(model=apps.get_model("product_details", "ProductDetailsFile"))


class Migration(migrations.Migration):

    dependencies = [
        ("product_details", "0001_initial"),
    ]

    operations = [migrations.RunPython(load_json_file_data)]
