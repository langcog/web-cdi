# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0014_study_waiver'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='confirm_completion',
            field=models.BooleanField(default=False),
        ),
    ]
