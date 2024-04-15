# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0024_auto_20160206_2101"),
    ]

    operations = [
        migrations.AlterField(
            model_name="backgroundinfo",
            name="age",
            field=models.IntegerField(
                null=True, verbose_name=b"Age (in months)", blank=True
            ),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="due_date_diff",
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name=b"By how many weeks?",
                validators=[
                    django.core.validators.MinValueValidator(
                        1, b"Number of weeks cannot be less than 1"
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="father_education",
            field=models.IntegerField(
                help_text=b"Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)",
                verbose_name=b"Father's (or Parent 2) Education",
                choices=[
                    (5, b"5"),
                    (6, b"6"),
                    (7, b"7"),
                    (8, b"8"),
                    (9, b"9"),
                    (10, b"10"),
                    (11, b"11"),
                    (12, b"12 (High school graduate)"),
                    (13, b"13"),
                    (14, b"14"),
                    (15, b"15"),
                    (16, b"16 (College graduate)"),
                    (17, b"17"),
                    (18, b"18 (Advanced degree)"),
                    (19, b"19"),
                    (20, b"20"),
                    (21, b"21"),
                    (22, b"22"),
                    (23, b"23 or more"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="language_days_per_week",
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name=b"How many days per week is the child exposed to these languages?",
                validators=[
                    django.core.validators.MaxValueValidator(
                        7, b"Number of days per week cannot exceed 7"
                    ),
                    django.core.validators.MinValueValidator(
                        1, b"Number of days per week cannot be less than 1"
                    ),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="language_from",
            field=models.CharField(
                max_length=50, null=True, verbose_name=b"From whom?", blank=True
            ),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="language_hours_per_day",
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name=b"How many hours per day is the child exposed to these languages?",
                validators=[
                    django.core.validators.MaxValueValidator(
                        24, b"Number of hours per day cannot exceed 24"
                    ),
                    django.core.validators.MinValueValidator(
                        1, b"Number of hours per day cannot be less than 1"
                    ),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="mother_education",
            field=models.IntegerField(
                help_text=b"Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)",
                verbose_name=b"Mother's (or Parent 1) Education",
                choices=[
                    (5, b"5"),
                    (6, b"6"),
                    (7, b"7"),
                    (8, b"8"),
                    (9, b"9"),
                    (10, b"10"),
                    (11, b"11"),
                    (12, b"12 (High school graduate)"),
                    (13, b"13"),
                    (14, b"14"),
                    (15, b"15"),
                    (16, b"16 (College graduate)"),
                    (17, b"17"),
                    (18, b"18 (Advanced degree)"),
                    (19, b"19"),
                    (20, b"20"),
                    (21, b"21"),
                    (22, b"22"),
                    (23, b"23 or more"),
                ],
            ),
        ),
    ]
