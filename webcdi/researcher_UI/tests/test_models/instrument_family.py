from django.test import TestCase, tag

from researcher_UI.models import InstrumentFamily

# models test


@tag("model")
class InstrumentFamilyModelTest(TestCase):
    def setUp(self) -> None:

        self.instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Model Test", chargeable=True
        )

    def test_instrument_family_creation(self):
        instance = self.instrument_family

        self.assertTrue(isinstance(instance, InstrumentFamily))
        self.assertEqual(instance.__str__(), f"{instance.name}")
