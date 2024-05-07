from django.contrib.auth.models import User
from django.test import TestCase, tag

from cdi_forms.models import Instrument_Forms
from researcher_UI.models import Instrument, InstrumentFamily
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model")
class InstrumentFormsModelTest(TestCase):

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

        self.instrument_form = Instrument_Forms(
            instrument=instrument, itemID="item_001", item="Some word", item_type="word"
        )
        return super().setUp()

    @tag("model")
    def test_administration_creation(self):
        instance = self.instrument_form

        self.assertTrue(isinstance(instance, Instrument_Forms))
        self.assertEqual(
            instance.__str__(),
            f"{instance.definition} ({instance.instrument.verbose_name}, {instance.itemID})",
        )

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = self.instrument_form

        # run test
        # response = c.get(get_admin_change_view_url(instance))
        # self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
