# Generated by Django 3.2 on 2022-12-10 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0065_auto_20220308_0702'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='instrument',
            options={'ordering': ['language', 'form', 'name']},
        ),
        migrations.AddField(
            model_name='instrument',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='participant_source_boolean',
            field=models.IntegerField(choices=[(0, 'None'), (1, 'Prolific'), (2, 'Centiment'), (3, 'RedCap'), (4, 'Lookit'), (5, 'Mturk'), (6, 'Qualtrics'), (99, 'Other')], default=0),
        ),
    ]