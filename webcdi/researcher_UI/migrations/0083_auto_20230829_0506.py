# Generated by Django 3.2.20 on 2023-08-29 05:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0082_auto_20230828_0541"),
    ]

    operations = [
        migrations.AddField(
            model_name="administration",
            name="completed_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="researcher",
            name="allowed_instruments",
            field=models.ManyToManyField(
                blank=True,
                to="researcher_UI.Instrument",
                verbose_name="Instruments this researcher has access to",
            ),
        ),
    ]
