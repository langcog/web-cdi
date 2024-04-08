from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Study, SummaryData)

# models test


@tag("model")
class SummaryDataModelTest(TestCase):
    def setUp(self) -> None:
        user = User.objects.create_user(
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

        study = Study.objects.create(
            researcher=user, name="Test Study Instance", instrument=instrument
        )
        administration = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash="qergfqewrfqwer",
            completed=False,
            due_date=timezone.now(),
        )

        self.summary_data = SummaryData.objects.create(
            administration=administration,
            title="Summary Data Title",
            value="Summary Data Value",
        )

    def test_summary_data_creation(self):
        instance = self.summary_data

        self.assertTrue(isinstance(instance, SummaryData))
        self.assertEqual(
            instance.__str__(), f"{instance.administration}: {instance.title}"
        )
