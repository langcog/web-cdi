# Generated by Django 4.2.8 on 2024-02-07 18:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0095_alter_administration_completed_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="payment_code",
            new_name="PaymentCode",
        ),
    ]
