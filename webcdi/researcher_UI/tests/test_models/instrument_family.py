from django.contrib.auth.models import User
from django.test import TestCase, tag

from researcher_UI.models import InstrumentFamily
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

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

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = self.instrument_family

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
