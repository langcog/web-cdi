# Generated by Django 3.2.18 on 2023-04-03 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0067_auto_20230303_1432'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstrumentFamily',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=51)),
                ('chargeable', models.BooleanField(default=False)),
            ],
        ),
    ]