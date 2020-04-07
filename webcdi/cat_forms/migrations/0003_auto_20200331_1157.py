# Generated by Django 2.2.6 on 2020-03-31 11:57

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cat_forms', '0002_auto_20200331_1147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catresponse',
            name='administered_items',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=101), null=True, size=None),
        ),
        migrations.AlterField(
            model_name='catresponse',
            name='administered_responses',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.BooleanField(), null=True, size=None),
        ),
    ]