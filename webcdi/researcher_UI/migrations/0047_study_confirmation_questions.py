# Generated by Django 2.2.6 on 2020-04-16 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0046_auto_20200329_1019"),
    ]

    operations = [
        migrations.AddField(
            model_name="study",
            name="confirmation_questions",
            field=models.BooleanField(default=False),
        ),
    ]
