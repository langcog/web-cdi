# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0009_auto_20161208_2055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instrument',
            name='form',
            field=models.CharField(max_length=51),
        ),
        migrations.AlterField(
            model_name='instrument',
            name='language',
            field=models.CharField(max_length=51),
        ),
        migrations.AlterField(
            model_name='instrument',
            name='max_age',
            field=models.IntegerField(default=0, verbose_name=b'Maximum age'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='instrument',
            name='min_age',
            field=models.IntegerField(default=0, verbose_name=b'Minimum age'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='instrument',
            unique_together=set([('language', 'form')]),
        ),
    ]
