# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-22 09:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mirror', '0010_auto_20160922_0918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalconfig',
            name='log_file',
            field=models.CharField(default=b'/product/oet/data/mirror.log', max_length=100),
        ),
    ]