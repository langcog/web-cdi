from django.test import TestCase, tag

from researcher_UI.models import (Benchmark, Instrument, InstrumentFamily,
                                  InstrumentScore)

# models test


@tag("model")
class BenchmarkModelTest(TestCase):
    def setUp(self) -> None:

        instrument_family, created = InstrumentFamily.objects.get_or_create(
            name="Instrument Family Test Model", chargeable=False
        )

        instrument, created = Instrument.objects.get_or_create(
            name="Test Instrument",
            language="Test Language",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        instrument_score, created = InstrumentScore.objects.get_or_create(
            instrument=instrument,
            title="Test Instrument Score",
            category="Test Instrument Score Category",
            scoring_measures="Test Instrument Score Measures",
        )

        self.benchmark = Benchmark.objects.create(
            instrument=instrument,
            instrument_score=instrument_score,
            percentile=95,
            age=15,
            raw_score=35,
            raw_score_boy=33,
            raw_score_girl=37,
        )

    def test_benchmark_creation(self):
        instance = self.benchmark

        self.assertTrue(isinstance(instance, Benchmark))
        self.assertEqual(
            instance.__str__(),
            f"{instance.instrument_score} {instance.percentile} {instance.age}",
        )
