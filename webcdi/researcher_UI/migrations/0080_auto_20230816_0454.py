# Generated by Django 3.2.20 on 2023-08-16 04:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0079_study_no_demographic_boolean'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='send_completion_flag_url',
            field=models.URLField(blank=True, help_text='Send completion flag to URL', null=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='no_demographic_boolean',
            field=models.BooleanField(default=False, help_text='You must include DOB, age offset and sex in the Link URL'),
        ),
    ]