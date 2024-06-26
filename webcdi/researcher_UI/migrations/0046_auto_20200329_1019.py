# Generated by Django 2.2.6 on 2020-03-29 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0045_administration_opt_out"),
    ]

    operations = [
        migrations.AlterField(
            model_name="administration",
            name="completedBackgroundInfo",
            field=models.BooleanField(
                default=False, verbose_name="Completed Background Info (P1)"
            ),
        ),
        migrations.AlterField(
            model_name="administration",
            name="completedSurvey",
            field=models.BooleanField(default=False, verbose_name="Completed Survey"),
        ),
    ]
