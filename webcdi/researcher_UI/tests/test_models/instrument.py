from django.test import TestCase, tag

from researcher_UI.models import Instrument, InstrumentFamily

# models test


@tag("model")
class InstrumentModelTest(TestCase):
    def setUp(self) -> None:

        instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=False
        )

        self.instrument = Instrument.objects.create(
            name="Test Instrument",
            language="Test Language",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )

    def test_instrument_creation(self):
        instance = self.instrument

        self.assertTrue(isinstance(instance, Instrument))
        self.assertEqual(instance.__str__(), f"{instance.verbose_name}")
        self.assertEqual(instance.item_count, 0)
