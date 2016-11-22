# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0028_auto_20161118_0033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundinfo',
            name='caregiver_info',
            field=models.IntegerField(verbose_name=b'Who does your child live with?', choices=[(2, b'Two parents'), (1, b'One parent'), (3, b'One parent plus other caregiver (e.g., grandparent)'), (0, b'Other caregivers (e.g., grandparent or grandparents)')]),
        ),
    ]
