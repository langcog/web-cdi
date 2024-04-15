from django.test import TestCase, tag

from researcher_UI.models import (Instrument, InstrumentFamily,
                                  InstrumentScore, Measure)
from researcher_UI.tests.utils import get_admin_change_view_url, get_admin_changelist_view_url
from django.contrib.auth.models import User
# models test


@tag("model")
class MeasureModelTest(TestCase):
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

        instrument_score = InstrumentScore.objects.create(
            instrument=instrument,
            title="Instrument Score Test Title",
            category="Instrument Score Test Category",
            scoring_measures="Instrument Score Test Measure",
        )

        self.measure = Measure.objects.create(
            instrument_score=instrument_score, key="Measure Test Key", value=1
        )

    def test_measure_creation(self):
        instance = self.measure

        self.assertTrue(isinstance(instance, Measure))
        self.assertEqual(
            instance.__str__(), f"{instance.instrument_score} {instance.key}"
        )
