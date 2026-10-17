# page_number used to hold the section a parent last posted from, and the form
# resumed at page_number + 1; it now holds the section to resume at (#719).
# Shift unfinished administrations so they resume exactly where they would have.

from django.db import migrations
from django.db.models import F


def forwards(apps, schema_editor):
    Administration = apps.get_model("researcher_UI", "Administration")
    Administration.objects.filter(completed=False, page_number__gt=0).update(
        page_number=F("page_number") + 1
    )


def backwards(apps, schema_editor):
    Administration = apps.get_model("researcher_UI", "Administration")
    Administration.objects.filter(completed=False, page_number__gt=1).update(
        page_number=F("page_number") - 1
    )


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0107_study_required_source_id"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
