# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-09-29 07:35
from __future__ import unicode_literals

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0039_merge_20190812_1054"),
    ]

    operations = [
        migrations.AlterField(
            model_name="study",
            name="waiver",
            field=ckeditor.fields.RichTextField(blank=True),
        ),
    ]
