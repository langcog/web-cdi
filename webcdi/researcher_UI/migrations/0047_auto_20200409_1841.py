# Generated by Django 2.2.6 on 2020-04-09 18:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0046_auto_20200329_1019"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="instrumentscore",
            name="measure",
        ),
        migrations.CreateModel(
            name="Measure",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=51)),
                ("value", models.IntegerField(default=0)),
                (
                    "instrument_score",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="researcher_UI.InstrumentScore",
                    ),
                ),
            ],
        ),
    ]
