# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-30 08:28
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mirror', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oracletarget',
            name='mysql_db',
            field=models.CharField(max_length=50, unique=True, validators=[django.core.validators.RegexValidator(inverse_match=True, message=b"Use '_' instead of ' '", regex=b' ')]),
        ),
        migrations.AlterField(
            model_name='oracletarget',
            name='redis_db',
            field=models.IntegerField(unique=True),
        ),
    ]
