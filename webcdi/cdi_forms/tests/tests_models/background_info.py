from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Study)
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model")
class BackgroundIndoModelTest(TestCase):

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
            researcher=user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        administration = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now(),
        )

        self.instance = BackgroundInfo.objects.create(
            administration=administration, age=12, source_id="123456"
        )

        return super().setUp()

    @tag("model")
    def test_administration_creation(self):
        instance = self.instance

        self.assertTrue(isinstance(instance, BackgroundInfo))
        self.assertEqual(instance.__str__(), f"{instance.administration}")

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = self.instance

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
