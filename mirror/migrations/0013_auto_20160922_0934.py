# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-22 09:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mirror', '0012_auto_20160922_0933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalconfig',
            name='log_size',
            field=models.IntegerField(default=10, help_text=b"Logfile's size, Unit is MB. Max is 32767 MB."),
        ),
    ]
