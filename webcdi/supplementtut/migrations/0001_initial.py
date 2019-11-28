# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_registration_profile_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyRegistrationSupplement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Please fill your full name here', max_length=101, verbose_name='Full name')),
                ('institution', models.CharField(max_length=101, verbose_name='Name of institution')),
                ('comments', models.TextField(verbose_name='Comments', blank=True)),
                ('registration_profile', models.OneToOneField(related_name='_supplementtut_myregistrationsupplement_supplement', editable=False, to='registration.RegistrationProfile', verbose_name='registration profile', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
