# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0017_english_wg'),
    ]

    operations = [
        migrations.AlterField(
            model_name='english_wg',
            name='uni_lemma',
            field=models.CharField(max_length=101, null=True),
        ),
    ]
