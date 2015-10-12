# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0009_backgroundinfo_born_on_due_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='backgroundinfo',
            name='born_on_due_date',
        ),
    ]
