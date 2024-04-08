from django.test import TestCase, tag

from researcher_UI.models import Instrument, InstrumentFamily, InstrumentScore

# models test


@tag("model")
class InstrumentScoreModelTest(TestCase):
    def setUp(self) -> None:

        instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=False
        )

        instrument = Instrument.objects.create(
            name="Test Instrument",
            language="Test Language",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        self.instrument_score = InstrumentScore.objects.create(
            instrument=instrument,
            title="Instrument Score Test Title",
            category="Instrument Score Test Category",
            scoring_measures="Instrument Score Test Measure",
        )

    def test_instrument_score_creation(self):
        instance = self.instrument_score

        self.assertTrue(isinstance(instance, InstrumentScore))
        self.assertEqual(instance.__str__(), f"{instance.instrument}: {instance.title}")
