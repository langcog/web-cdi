# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-09-29 08:08
from __future__ import unicode_literals

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0040_auto_20190929_0735"),
    ]

    operations = [
        migrations.AlterField(
            model_name="study",
            name="waiver",
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
    ]
