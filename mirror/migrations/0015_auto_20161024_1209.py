# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-10-24 12:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mirror', '0014_globalconfig_log_format'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalconfig',
            name='processes',
            field=models.IntegerField(default=4, help_text=b'Max number of processes.(Unusable)'),
        ),
        migrations.AlterField(
            model_name='globalconfig',
            name='run',
            field=models.BooleanField(default=True, help_text=b'Do you want to start or stop this model at web level.(Unusable)'),
        ),
    ]
