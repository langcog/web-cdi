# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0033_auto_20170508_2005"),
    ]

    operations = [
        migrations.AddField(
            model_name="backgroundinfo",
            name="multi_birth",
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name=b"Twins, triplets, quadruplets, other?",
                choices=[
                    (2, b"Twins"),
                    (3, b"Triplets"),
                    (4, b"Quadruplets"),
                    (5, b"Quintuplets or greater"),
                ],
            ),
        ),
        migrations.AddField(
            model_name="backgroundinfo",
            name="multi_birth_boolean",
            field=models.IntegerField(
                default=2,
                verbose_name=b"Was your child born as part of a multiple birth?",
            ),
            preserve_default=False,
        ),
    ]
