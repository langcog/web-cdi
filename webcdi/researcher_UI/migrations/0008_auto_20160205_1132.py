# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0007_administration_completedbackgroundinfo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administration_data',
            name='value',
            field=models.CharField(max_length=200),
        ),
    ]
