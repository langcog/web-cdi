# Generated by Django 3.2 on 2022-10-14 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0083_auto_20220308_0702"),
    ]

    operations = [
        migrations.AddField(
            model_name="choices",
            name="choice_set_fr",
            field=models.CharField(max_length=101, null=True),
        ),
    ]
