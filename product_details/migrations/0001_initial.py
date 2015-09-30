# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductDetailsFile',
            fields=[
                ('name', models.CharField(max_length=250, serialize=False, primary_key=True)),
                ('content', models.TextField(blank=True)),
                ('last_modified', models.CharField(help_text=b'Value of Last-Modified HTTP header',
                                                   max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
