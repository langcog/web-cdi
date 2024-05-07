from django.contrib.auth.models import User
from django.test import TestCase, tag

from researcher_UI.models import Instrument, InstrumentFamily, Study
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

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

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = self.study

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
