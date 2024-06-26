# Generated by Django 2.2.13 on 2020-10-28 10:09

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0055_merge_20200916_0933"),
    ]

    operations = [
        migrations.AddField(
            model_name="study",
            name="end_message",
            field=models.CharField(
                choices=[
                    ("standard", "Standard"),
                    ("bespoke", "Bespoke"),
                    ("combined", "Combined"),
                ],
                default="standard",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="study",
            name="end_message_text",
            field=ckeditor_uploader.fields.RichTextUploadingField(
                blank=True, null=True
            ),
        ),
    ]
