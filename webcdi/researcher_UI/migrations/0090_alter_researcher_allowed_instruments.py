# Generated by Django 3.2.20 on 2023-08-30 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0089_alter_researcher_allowed_instruments"),
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
    ]
