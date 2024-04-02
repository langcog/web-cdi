# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0002_auto_20150910_0648"),
    ]

    operations = [
        migrations.AlterField(
            model_name="study",
            name="name",
            field=models.CharField(max_length=51),
        ),
        migrations.AlterUniqueTogether(
            name="administration",
            unique_together=set([("study", "subject_id", "repeat_num")]),
        ),
        migrations.AlterUniqueTogether(
            name="administration_data",
            unique_together=set([("administration", "item_ID")]),
        ),
        migrations.AlterUniqueTogether(
            name="study",
            unique_together=set([("researcher", "name")]),
        ),
    ]
