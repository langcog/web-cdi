# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0020_study_test_period'),
    ]

    operations = [
        migrations.CreateModel(
            name='ip_address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip_address', models.CharField(max_length=30)),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name=b'Date IP address was added to database')),
                ('study', models.ForeignKey(to='researcher_UI.study', on_delete=models.PROTECT)),
            ],
        ),
    ]
