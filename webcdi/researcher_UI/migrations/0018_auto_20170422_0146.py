# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0017_auto_20170414_2219'),
    ]

    operations = [
        migrations.CreateModel(
            name='payment_code',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hash_id', models.CharField(max_length=128, unique=True, null=True)),
                ('added_date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date code was added to database')),
                ('assignment_date', models.DateTimeField(null=True, verbose_name=b'Date code was given to participant')),
                ('payment_type', models.CharField(max_length=50)),
                ('gift_amount', models.DecimalField(verbose_name=b'Monetary value', max_digits=6, decimal_places=2)),
                ('gift_code', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='study',
            name='allow_payment',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='study',
            name='allow_sharing',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payment_code',
            name='study',
            field=models.ForeignKey(to='researcher_UI.study'),
        ),
        migrations.AlterUniqueTogether(
            name='payment_code',
            unique_together=set([('payment_type', 'gift_code')]),
        ),
    ]
