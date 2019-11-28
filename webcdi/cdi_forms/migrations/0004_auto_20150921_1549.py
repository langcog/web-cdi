# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0003_backgroundinfo_administration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundinfo',
            name='administration',
            field=models.ForeignKey(to='researcher_UI.administration', unique=True, on_delete=models.PROTECT),
        ),
    ]
