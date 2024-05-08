from django.contrib.auth.models import User
from django.test import TestCase, tag

from researcher_UI.models import (Benchmark, Instrument, InstrumentFamily,
                                  InstrumentScore)
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

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

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = self.benchmark

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
