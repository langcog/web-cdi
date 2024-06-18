from django.core.management import call_command
from django.test import TestCase, tag

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
        self.assertEqual(len(instruments), 26)

    def test_populate_scoring(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)
        call_command("02_populate_instrument", *args, **opts)
        call_command("03_populate_scoring", *args, **opts)

        scores = InstrumentScore.objects.all()
        self.assertEqual(len(scores), 175)

    def test_populate_benchmark(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)
        call_command("02_populate_instrument", *args, **opts)
        call_command("03_populate_scoring", *args, **opts)
        call_command("04_populate_benchmark", *args, **opts)

        items = Benchmark.objects.all()
        self.assertEqual(len(items), 8650)

    def test_populate_choices(self):
        args = []
        opts = {}
        call_command("01_populate_instrument_family", *args, **opts)
        call_command("02_populate_instrument", *args, **opts)
        call_command("03_populate_scoring", *args, **opts)
        call_command("04_populate_benchmark", *args, **opts)
        call_command("05_populate_choices", *args, **opts)

        items = Choices.objects.all()
        self.assertEqual(len(items), 10)

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
        self.assertEqual(len(items), 10560)
