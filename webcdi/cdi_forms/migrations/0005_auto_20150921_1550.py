# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0004_auto_20150921_1549'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundinfo',
            name='administration',
            field=models.OneToOneField(to='researcher_UI.administration', on_delete=models.PROTECT),
        ),
    ]
