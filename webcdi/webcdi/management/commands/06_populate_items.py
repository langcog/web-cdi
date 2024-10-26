import csv
import json
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from cdi_forms.models import *
from researcher_UI.models import *

# Populates the ItemInfo and ItemMap models with data from instrument definition files.
# Given no arguments, does so for all instruments in 'static/json/instruments.json'.
# Given a language with -l and a form with -f, does so for only their Instrument object.


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [cell for cell in row]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-l", "--language", type=str)
        parser.add_argument("-f", "--form", type=str)

    def handle(self, *args, **options):
        PROJECT_ROOT = settings.BASE_DIR
        instruments = json.load(
            open(
                os.path.realpath(PROJECT_ROOT + "/static/json/instruments.json"),
                encoding="utf8",
            )
        )
        if options["language"] and options["form"]:
            input_language, input_form = options["language"], options["form"]
            input_instruments = filter(
                lambda instrument: instrument["language"] == input_language
                and instrument["form"] == input_form,
                instruments,
            )
        elif options["language"] and not options["form"]:
            input_language = options["language"]
            input_instruments = filter(
                lambda instrument: instrument["language"] == input_language, instruments
            )
        elif not options["language"] and options["form"]:
            input_form = options["form"]
            input_instruments = filter(
                lambda instrument: instrument["form"] == input_form, instruments
            )
        else:
            input_instruments = instruments

        for curr_instrument in input_instruments:
            if curr_instrument["form"] in settings.CAT_FORMS:
                continue

            instrument_language, instrument_form = (
                curr_instrument["language"],
                curr_instrument["form"],
            )

            instrument_obj = Instrument.objects.get(
                form=instrument_form, language=instrument_language
            )
            instrument_forms = apps.get_model(
                app_label="cdi_forms", model_name="Instrument_Forms"
            )

            print(f"    Populating items for {instrument_language}, {instrument_form}")

            ftype = curr_instrument["csv_file"].split(".")[-1]

            if ftype == "csv":
                contents = list(
                    unicode_csv_reader(
                        open(
                            os.path.realpath(
                                PROJECT_ROOT + "/" + curr_instrument["csv_file"]
                            ),
                            encoding="utf8",
                        )
                    )
                )
                col_names = contents[0]
                nrows = len(contents)
                get_row = lambda row: contents[row]
            else:
                raise IOError("Instrument file must be a CSV.")

            for row in range(1, nrows):
                row_values = get_row(row)
                if len(row_values) > 1:
                    itemID = row_values[col_names.index("itemID")]
                    item = row_values[col_names.index("item")]
                    item_type = row_values[col_names.index("item_type")]
                    item_category = row_values[col_names.index("category")]
                    item_choices = row_values[col_names.index("choices")]
                    choices_key = None
                    if "example" not in item_type:
                        try:
                            choices_key = Choices.objects.get(choice_set=item_choices)
                        except:
                            print(
                                f"{item}, {item_type}, {item_category}, {item_choices}"
                            )
                            raise IOError(
                                "Can't find choice set %s in model for %s"
                                % (
                                    item_category,
                                    itemID,
                                )
                            )

                    definition = row_values[col_names.index("definition")]
                    gloss = row_values[col_names.index("gloss")]
                    if "complexity_category" in col_names:
                        complexity_category = row_values[
                            col_names.index("complexity_category")
                        ]
                    else:
                        complexity_category = None

                    if "uni_lemma" in col_names:
                        uni_lemma = row_values[col_names.index("uni_lemma")]
                    else:
                        uni_lemma = None

                    if "scoring_category" in col_names:
                        scoring_category = row_values[
                            col_names.index("scoring_category")
                        ]
                        if len(scoring_category) < 1:
                            scoring_category = item_type
                    else:
                        scoring_category = item_type

                    if "enabler" in col_names:
                        enabler = row_values[col_names.index("enabler")]
                    else:
                        enabler = None

                    if "enable_response" in col_names:
                        enable_response = row_values[col_names.index("enable_response")]
                    else:
                        enable_response = None

                    data_dict = {
                        "item": item,
                        "item_type": item_type,
                        "category": item_category,
                        "choices": choices_key,
                        "definition": definition,
                        "gloss": gloss,
                        "complexity_category": complexity_category,
                        "uni_lemma": uni_lemma,
                        "item_order": row,
                        "scoring_category": scoring_category,
                        "enabler": enabler,
                        "enable_response": enable_response,
                    }

                    cdi_item, created = instrument_forms.objects.update_or_create(
                        instrument=instrument_obj,
                        itemID=itemID,
                        defaults=data_dict,
                    )
