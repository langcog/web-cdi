# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0018_auto_20170422_0146'),
    ]

    operations = [
        migrations.AddField(
            model_name='administration',
            name='bypass',
            field=models.NullBooleanField(default=None, verbose_name=b'Willing to forgo payment'),
        ),
        migrations.AddField(
            model_name='administration',
            name='include',
            field=models.NullBooleanField(default=True, verbose_name=b'Include for eventual analysis'),
        ),
    ]
