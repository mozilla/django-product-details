#!/usr/bin/env python
import os

import django
from django.core.management import call_command

if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()
    call_command("update_product_details")
