# Generated by Django 3.2.20 on 2023-09-04 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0093_auto_20230904_0715'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='study',
            name='api_token',
        ),
        migrations.AlterField(
            model_name='researcher',
            name='allowed_instruments',
            field=models.ManyToManyField(blank=True, to='researcher_UI.Instrument', verbose_name='Instruments this researcher has access to'),
        ),
    ]