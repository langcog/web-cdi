# Generated by Django 2.2.13 on 2021-07-28 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0080_update_choice_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="backgroundinfo",
            name="place_of_residence",
            field=models.CharField(
                blank=True,
                max_length=51,
                null=True,
                verbose_name="Place of residence (neighnorhood/district)",
            ),
        ),
        migrations.AddField(
            model_name="backgroundinfo",
            name="primary_caregiver_occupation",
            field=models.CharField(
                blank=True,
                max_length=51,
                null=True,
                verbose_name="Primary caregiver occupation",
            ),
        ),
        migrations.AddField(
            model_name="backgroundinfo",
            name="primary_caregiver_occupation_description",
            field=models.CharField(
                blank=True,
                max_length=51,
                null=True,
                verbose_name="Primary caregiver occupation description",
            ),
        ),
        migrations.AddField(
            model_name="backgroundinfo",
            name="secondary_caregiver_occupation",
            field=models.CharField(
                blank=True,
                max_length=51,
                null=True,
                verbose_name="Secondary caregiver occupation",
            ),
        ),
        migrations.AddField(
            model_name="backgroundinfo",
            name="secondary_caregiver_occupation_description",
            field=models.CharField(
                blank=True,
                max_length=51,
                null=True,
                verbose_name="Secondary caregiver occupation description",
            ),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="father_education",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (5, "5"),
                    (6, "6"),
                    (7, "7"),
                    (8, "8"),
                    (9, "9"),
                    (10, "10"),
                    (11, "11"),
                    (12, "12"),
                    (13, "13"),
                    (14, "14"),
                    (15, "15"),
                    (16, "16"),
                    (17, "17"),
                    (18, "18"),
                    (19, "19"),
                    (20, "20"),
                    (21, "21"),
                    (22, "22"),
                    (23, "23"),
                    (0, "Prefer not to disclose"),
                ],
                help_text="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)",
                null=True,
                verbose_name="Secondary Caregiver Education",
            ),
        ),
        migrations.AlterField(
            model_name="backgroundinfo",
            name="mother_education",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (5, "5"),
                    (6, "6"),
                    (7, "7"),
                    (8, "8"),
                    (9, "9"),
                    (10, "10"),
                    (11, "11"),
                    (12, "12"),
                    (13, "13"),
                    (14, "14"),
                    (15, "15"),
                    (16, "16"),
                    (17, "17"),
                    (18, "18"),
                    (19, "19"),
                    (20, "20"),
                    (21, "21"),
                    (22, "22"),
                    (23, "23"),
                    (0, "Prefer not to disclose"),
                ],
                help_text="Choose highest grade completed (12 = high school graduate; 16 = college graduate; 18 = advanced degree)",
                null=True,
                verbose_name="Primary Caregiver Education",
            ),
        ),
    ]
