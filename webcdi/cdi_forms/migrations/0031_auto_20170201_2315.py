# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0030_auto_20170105_0124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundinfo',
            name='birth_order',
            field=models.IntegerField(verbose_name=b'Birth order', choices=[(1, b'1 (First)'), (2, b'2 (Second)'), (3, b'3 (Third)'), (4, b'4 (Fourth)'), (5, b'5 (Fifth)'), (6, b'6 (Sixth)'), (7, b'7 (Seventh)'), (8, b'8 (Eighth)'), (9, b'9 (Ninth)'), (10, b'10 or more (Tenth or Later)'), (0, b'Prefer not to disclose')]),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='birth_weight',
            field=models.FloatField(verbose_name=b'Birth weight', choices=[(1.0, b'Less than 3 lbs, 0 oz'), (3.0, b'3 lbs, 0 oz - 3 lbs, 7 oz'), (3.5, b'3 lbs, 8 oz - 3 lbs, 15 oz'), (4.0, b'4 lbs, 0 oz - 4 lbs, 7 oz'), (4.5, b'4 lbs, 8 oz - 4 lbs, 15 oz'), (5.0, b'5 lbs, 0 oz - 5 lbs, 7 oz'), (5.5, b'5 lbs, 8 oz - 5 lbs, 15 oz'), (6.0, b'6 lbs, 0 oz - 6 lbs, 7 oz'), (6.5, b'6 lbs, 8 oz - 6 lbs, 15 oz'), (7.0, b'7 lbs, 0 oz - 7 lbs, 7 oz'), (7.5, b'7 lbs, 8 oz - 7 lbs, 15 oz'), (8.0, b'8 lbs, 0 oz - 8 lbs, 7 oz'), (8.5, b'8 lbs, 8 oz - 8 lbs, 15 oz'), (9.0, b'9 lbs, 0 oz - 9 lbs, 7 oz'), (9.5, b'9 lbs, 8 oz - 9 lbs, 15 oz'), (10.0, b'10 lbs, 0 oz or more'), (0.0, b'Prefer not to disclose')]),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='born_on_due_date',
            field=models.IntegerField(verbose_name=b'Was your child born earlier or later than their due date?'),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='caregiver_info',
            field=models.IntegerField(verbose_name=b'Who does your child live with?', choices=[(2, b'Two parents'), (1, b'One parent'), (3, b'One parent plus other caregiver (e.g., grandparent)'), (4, b'Other caregivers (e.g., grandparent or grandparents)'), (0, b'Prefer not to disclose')]),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='ear_infections_boolean',
            field=models.IntegerField(verbose_name=b'Has your child experienced chronic ear infections (5 or more)? '),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='hearing_loss_boolean',
            field=models.IntegerField(verbose_name=b'Do you suspect that your child may have hearing loss?'),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='illnesses_boolean',
            field=models.IntegerField(verbose_name=b'Has your child had any major illnesses, hospitalizations, or diagnosed disabilities?'),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='learning_disability_boolean',
            field=models.IntegerField(verbose_name=b'Have you or anyone in your immediate family been diagnosed with a language or learning disability?'),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='other_languages_boolean',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='services_boolean',
            field=models.IntegerField(verbose_name=b'Has your child ever received any services for speech, language, or development issues?'),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='vision_problems_boolean',
            field=models.IntegerField(verbose_name=b'Is there some reason to suspect that your child may have vision problems?'),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='worried_boolean',
            field=models.IntegerField(verbose_name=b"Are you worried about your child's progress in language or communication?"),
        ),
    ]
