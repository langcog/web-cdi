from django.contrib.auth.models import User
from django.test import TestCase, tag

from researcher_UI.models import Instrument, InstrumentFamily, InstrumentScore
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

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

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = self.instrument_score

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
