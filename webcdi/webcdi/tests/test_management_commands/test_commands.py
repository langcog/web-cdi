from django.core.management import call_command
from django.test import TestCase

from cdi_forms.models import Choices, Instrument_Forms
from researcher_UI.models import (Benchmark, Instrument, InstrumentFamily,
                                  InstrumentScore)


class CommandsTestCase(TestCase):
    def test_populate_instrument_family(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)

        families = InstrumentFamily.objects.all()
        self.assertEqual(len(families), 13)

    def test_populate_instrument(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)
        call_command("02_populate_instrument", *args, **opts)

        instruments = Instrument.objects.all()
        self.assertEqual(len(instruments), 29)

    def test_populate_scoring(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)
        call_command("02_populate_instrument", *args, **opts)
        call_command("03_populate_scoring", *args, **opts)

        scores = InstrumentScore.objects.all()
        self.assertEqual(len(scores), 201)

        # re-running updates in place (instrument + title are unique, #675)
        call_command("03_populate_scoring", *args, **opts)
        self.assertEqual(InstrumentScore.objects.count(), 201)

    def test_populate_benchmark(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)
        call_command("02_populate_instrument", *args, **opts)
        call_command("03_populate_scoring", *args, **opts)
        call_command("04_populate_benchmark", *args, **opts)

        items = Benchmark.objects.all()
        # WS norms run 16-36 months (#767): 3,600 rows for 31-36, and the
        # English WS file is shared with Canadian English WS
        self.assertEqual(len(items), 53494)
        self.assertEqual(
            Benchmark.objects.get(
                instrument__name="English_WS", instrument_score__title="Total Produced",
                age=36, percentile=50,
            ).raw_score,
            643,  # Wordbank / 2023 manual norms, extrapolated to 36 months
        )

    def test_populate_choices(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)
        call_command("02_populate_instrument", *args, **opts)
        call_command("03_populate_scoring", *args, **opts)
        call_command("04_populate_benchmark", *args, **opts)
        call_command("05_populate_choices", *args, **opts)

        items = Choices.objects.all()
        self.assertEqual(len(items), 14)

    def test_populate_items(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)
        call_command("02_populate_instrument", *args, **opts)
        call_command("03_populate_scoring", *args, **opts)
        call_command("04_populate_benchmark", *args, **opts)
        call_command("05_populate_choices", *args, **opts)
        call_command("06_populate_items", *args, **opts)

        items = Instrument_Forms.objects.all()
        self.assertEqual(len(items), 10967)

    def test_reload_restores_changed_items_and_benchmarks(self):
        # #685: the bulk loaders must leave the same rows as update_or_create
        # did: changed rows are rewritten, missing rows recreated, the rest
        # left alone
        for step in [
            "01_populate_instrument_family",
            "02_populate_instrument",
            "03_populate_scoring",
            "04_populate_benchmark",
            "05_populate_choices",
            "06_populate_items",
        ]:
            call_command(step)

        def snapshot():
            items = sorted(
                Instrument_Forms.objects.values_list(
                    "instrument__name", "itemID", "item", "definition",
                    "item_order", "choices__choice_set_en",
                )
            )
            benchmarks = sorted(
                Benchmark.objects.values_list(
                    "instrument__name", "instrument_score__title", "percentile",
                    "age", "raw_score", "raw_score_boy", "raw_score_girl",
                )
            )
            return items, benchmarks

        loaded = snapshot()
        changed = Instrument_Forms.objects.order_by("pk")[:5]
        Instrument_Forms.objects.filter(pk__in=[i.pk for i in changed]).update(
            definition="stale", item_order=9999, choices=None
        )
        Instrument_Forms.objects.filter(
            pk__in=Instrument_Forms.objects.order_by("-pk").values("pk")[:5]
        ).delete()
        Benchmark.objects.filter(
            pk__in=Benchmark.objects.order_by("pk").values("pk")[:5]
        ).update(raw_score=-1)
        Benchmark.objects.filter(
            pk__in=Benchmark.objects.order_by("-pk").values("pk")[:5]
        ).delete()

        call_command("04_populate_benchmark")
        call_command("06_populate_items")
        self.assertEqual(snapshot(), loaded)
