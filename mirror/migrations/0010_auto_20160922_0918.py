# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-22 09:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mirror', '0009_auto_20160922_0916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalconfig',
            name='log_file',
            field=models.FilePathField(default=b'/product/oet/data/mirror.log', path=b'/product/oet', recursive=True),
        ),
    ]
