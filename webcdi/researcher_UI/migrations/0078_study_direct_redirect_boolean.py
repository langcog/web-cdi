# Generated by Django 3.2.20 on 2023-08-15 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0077_administration_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="study",
            name="direct_redirect_boolean",
            field=models.BooleanField(
                default=True,
                help_text="Deselect this if the redirect url calls an API to get the actual redirect url",
            ),
        ),
    ]
