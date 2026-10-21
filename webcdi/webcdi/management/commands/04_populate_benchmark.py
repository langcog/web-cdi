import csv
import json
import os
import re

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
            instrument_language, instrument_form = (
                curr_instrument["language"],
                curr_instrument["form"],
            )

            if not "benchmark" in curr_instrument:
                print("    No Benchmark data for", instrument_language, instrument_form)
                continue

            print(
                "    Populating Benchmark data for",
                instrument_language,
                instrument_form,
            )

            instrument_obj = Instrument.objects.get(
                form=instrument_form, language=instrument_language
            )

            ftype = curr_instrument["csv_file"].split(".")[-1]

            if ftype == "csv":

                contents = list(
                    unicode_csv_reader(
                        open(
                            os.path.realpath(
                                PROJECT_ROOT + "/" + curr_instrument["benchmark"]
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

            # One query per instrument for its scores and existing benchmarks,
            # then bulk writes, instead of 3 queries per row (#685). Same
            # result as update_or_create row by row: a repeated
            # (score, percentile, age) keeps its last row's values.
            scores = {
                score.title: score
                for score in InstrumentScore.objects.filter(instrument=instrument_obj)
            }
            existing = {}
            for b in Benchmark.objects.filter(instrument=instrument_obj):
                key = (b.instrument_score_id, b.percentile, b.age)
                if key in existing:
                    # update_or_create would have raised here too
                    raise Benchmark.MultipleObjectsReturned(
                        f"{instrument_obj} has more than one benchmark {key}"
                    )
                existing[key] = b
            to_create, to_update = {}, {}
            for row in range(1, nrows):
                row_values = get_row(row)
                if len(row_values) > 1:
                    title = row_values[col_names.index("title")]
                    if title not in scores:
                        raise InstrumentScore.DoesNotExist(
                            f"No InstrumentScore {title!r} for {instrument_obj}"
                        )
                    scoring_obj = scores[title]
                    percentile = row_values[col_names.index("percentile")]
                    age = row_values[col_names.index("age")]
                    raw_score = row_values[col_names.index("raw_score")]
                    raw_score_boy = row_values[col_names.index("raw_score_boy")]
                    raw_score_girl = row_values[col_names.index("raw_score_girl")]
                    data_dict = {
                        "raw_score": raw_score,
                        "raw_score_boy": raw_score_boy,
                        "raw_score_girl": raw_score_girl,
                    }

                    key = (scoring_obj.pk, int(percentile), int(age))
                    if key in existing:
                        benchmark = existing[key]
                        to_update[key] = benchmark
                    elif key in to_create:
                        benchmark = to_create[key]
                    else:
                        benchmark = Benchmark(
                            instrument=instrument_obj,
                            instrument_score=scoring_obj,
                            percentile=percentile,
                            age=age,
                        )
                        to_create[key] = benchmark
                    for field, value in data_dict.items():
                        setattr(benchmark, field, value)

            Benchmark.objects.bulk_create(to_create.values(), batch_size=1000)
            Benchmark.objects.bulk_update(
                to_update.values(),
                ["raw_score", "raw_score_boy", "raw_score_girl"],
                batch_size=1000,
            )
