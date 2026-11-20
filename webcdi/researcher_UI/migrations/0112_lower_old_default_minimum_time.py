from django.db import migrations


def lower_old_default(apps, schema_editor):
    """Groups still at the old 6-minute default get their form's new default
    (#808): 3 minutes for Words & Gestures and Words & Sentences, 2 otherwise.
    A group set to 6 on purpose can't be told apart; researchers can set it
    again. Other values are left alone."""
    Study = apps.get_model("researcher_UI", "Study")
    # copied from default_minimum_time: migrations must not import app code
    full = Study.objects.filter(timing=6, instrument__form__in=["WG", "WS"])
    full.update(timing=3)
    Study.objects.filter(timing=6).update(timing=2)


class Migration(migrations.Migration):

    dependencies = [
        ("researcher_UI", "0111_study_default_minimum_time"),
    ]

    operations = [
        migrations.RunPython(lower_old_default, migrations.RunPython.noop),
    ]
