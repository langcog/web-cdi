# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-09-29 07:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0061_auto_20190802_1443"),
    ]

    operations = [
        migrations.AlterField(
            model_name="backgroundinfo",
            name="birth_weight_kg",
            field=models.FloatField(blank=True, null=True, verbose_name="Birth weight"),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="birth_weight_lb",
            field=models.FloatField(blank=True, null=True, verbose_name="Birth weight"),
        ),
    ]
