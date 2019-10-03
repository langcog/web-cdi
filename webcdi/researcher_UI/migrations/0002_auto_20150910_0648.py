# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('researcher_UI', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='administration',
            name='researcher',
        ),
        migrations.AddField(
            model_name='study',
            name='researcher',
            field=models.ForeignKey(default=0, to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT),
            preserve_default=False,
        ),
    ]
