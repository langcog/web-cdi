from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Study, administration_data)
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model")
class AdministrationDataModelTest(TestCase):

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

        self.administration_data = administration_data.objects.create(
            administration=administration,
            item_ID="Administration data test Item ID",
            value=1,
        )

        return super().setUp()

    def test_administration_creation(self):
        instance = self.administration_data

        self.assertTrue(isinstance(instance, administration_data))
        self.assertEqual(
            instance.__str__(), f"{instance.administration} {instance.item_ID}"
        )

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = self.administration_data

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
