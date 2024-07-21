import json
import os
import string

from django.conf import settings
from django.core.management.base import BaseCommand

from researcher_UI.models import InstrumentFamily

# Populates the ItemInfo and ItemMap models with data from instrument definition files.
# Given no arguments, does so for all instruments in 'static/json/instruments.json'.
# Given a language with -l and a form with -f, does so for only their Instrument object.


class Command(BaseCommand):

    def handle(self, *args, **options):
        PROJECT_ROOT = settings.BASE_DIR
        families = json.load(
            open(
                os.path.realpath(
                    PROJECT_ROOT + "/static/json/instrument_families.json"
                ),
                encoding="utf8",
            )
        )
        var_safe = lambda s: "".join(
            [
                c
                for c in "_".join(s.split())
                if c in string.ascii_letters + string.digits + "_"
            ]
        )

        for family in families:
            family_name = family["name"]

            print(f"Updating instrument table for {family_name}")

            data_dict = {"chargeable": family["chargeable"]}

            family_obj, created = InstrumentFamily.objects.update_or_create(
                name=family_name,
                defaults=data_dict,
            )

            if created:
                created = "created"
            else:
                created = "updated"

            print(f"{family_obj} {created}")
