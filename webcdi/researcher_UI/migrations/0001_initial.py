# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='administration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject_id', models.IntegerField()),
                ('repeat_num', models.IntegerField()),
                ('url_hash', models.CharField(max_length=128)),
                ('researcher', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='administration_data',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('item_ID', models.CharField(max_length=101)),
                ('value', models.CharField(max_length=101)),
                ('administration', models.ForeignKey(to='researcher_UI.administration', on_delete=models.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='instrument',
            fields=[
                ('name', models.CharField(max_length=51, serialize=False, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='study',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=51)),
                ('instrument', models.ForeignKey(to='researcher_UI.instrument', on_delete=models.PROTECT)),
            ],
        ),
        migrations.AddField(
            model_name='administration',
            name='study',
            field=models.ForeignKey(to='researcher_UI.study', on_delete=models.PROTECT),
        ),
    ]
