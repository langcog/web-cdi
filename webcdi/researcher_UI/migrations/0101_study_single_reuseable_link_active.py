# Generated by Django 4.2.20 on 2025-06-21 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0100_administration_send_completion_flag_url_response"),
    ]

    operations = [
        migrations.AddField(
            model_name="study",
            name="single_reuseable_link_active",
            field=models.BooleanField(default=True),
        ),
    ]
