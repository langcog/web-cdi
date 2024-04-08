from django.contrib.auth.models import User
from django.test import TestCase, tag

from researcher_UI.models import Instrument, InstrumentFamily, Study

# models test


@tag("model")
class StudyModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

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

        self.study = Study.objects.create(
            researcher=self.user, name="Test Study Instance", instrument=instrument
        )

        chargeable_instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Chargeable Model", chargeable=True
        )

        chargeable_instrument = Instrument.objects.create(
            name="Test Instrument Chargeable",
            language="Chargeable Test Language",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=chargeable_instrument_family,
        )

        self.chargeable_study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance Chargeable",
            instrument=chargeable_instrument,
        )

    def test_study_creation(self):
        instance = self.study

        self.assertTrue(isinstance(instance, Study))
        self.assertEqual(instance.__str__(), f"{instance.name}")
        self.assertTrue(instance.valid_code(self.user))

    def test_study_for_chargeable_instrument_creation(self):
        instance = self.chargeable_study

        self.assertTrue(isinstance(instance, Study))
        self.assertEqual(instance.__str__(), f"{instance.name}")
        self.assertFalse(instance.valid_code(self.user))
