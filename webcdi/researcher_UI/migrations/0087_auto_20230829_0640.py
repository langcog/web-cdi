# Generated by Django 3.2.20 on 2023-08-29 06:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0086_auto_20230829_0631"),
    ]

    operations = [
        migrations.AlterField(
            model_name="researcher",
            name="allowed_instruments",
            field=models.ManyToManyField(
                blank=True,
                to="researcher_UI.Instrument",
                verbose_name="Instruments this researcher has access to",
            ),
        ),
        migrations.AlterField(
            model_name="study",
            name="completion_data",
            field=models.JSONField(
                blank=True,
                help_text="Data to be included in the completion url.",
                null=True,
            ),
        ),
    ]
