# Generated by Django 3.2.18 on 2023-04-05 13:57

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("researcher_UI", "0070_researcher_allowed_instrument_families"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="instrumentfamily",
            options={
                "ordering": ["name"],
                "verbose_name_plural": "Instrument Families",
            },
        ),
    ]
