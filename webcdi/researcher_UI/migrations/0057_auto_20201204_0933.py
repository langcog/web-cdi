# Generated by Django 2.2.13 on 2020-12-04 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0056_auto_20201028_1009"),
    ]

    operations = [
        migrations.CreateModel(
            name="Demographic",
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
                ("name", models.CharField(max_length=30)),
                ("path", models.CharField(max_length=255)),
            ],
        ),
        migrations.AlterField(
            model_name="study",
            name="end_message",
            field=models.CharField(
                choices=[
                    ("standard", "Standard"),
                    ("bespoke", "Custom"),
                    ("combined", "Combined"),
                ],
                default="standard",
                max_length=10,
            ),
        ),
    ]
