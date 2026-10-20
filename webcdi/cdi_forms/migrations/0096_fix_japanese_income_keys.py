# The Japanese background form stored three income answers under the wrong
# keys (two of them US-dollar keys); see #665. Only rows collected with that
# form are touched, since other forms use "50000-75000" etc. legitimately.

from django.db import migrations

JAPANESE_FORM = "Japanese_no_NIH.json"
WRONG_TO_RIGHT = {
    "300-450": "300-400",
    "50000-75000": "400-500",
    "75000-100000": "500-600",
}


def remap(apps, mapping):
    BackgroundInfo = apps.get_model("cdi_forms", "BackgroundInfo")
    rows = BackgroundInfo.objects.filter(
        administration__study__demographic__path__endswith=JAPANESE_FORM
    )
    for old, new in mapping.items():
        rows.filter(annual_income=old).update(annual_income=new)


def forwards(apps, schema_editor):
    remap(apps, WRONG_TO_RIGHT)


def backwards(apps, schema_editor):
    remap(apps, {new: old for old, new in WRONG_TO_RIGHT.items()})


class Migration(migrations.Migration):

    dependencies = [
        ("cdi_forms", "0095_alter_backgroundinfo_father_yob_and_more"),
        ("researcher_UI", "0107_study_required_source_id"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
