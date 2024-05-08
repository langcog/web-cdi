from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from researcher_UI.models import (Instrument, InstrumentFamily, Study,
                                  ip_address)
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model")
class IPAddressModelTest(TestCase):
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
            researcher=user, name="Test Study Name", instrument=instrument
        )

        self.ip_address = ip_address.objects.create(
            study=study, ip_address="192.01.01.02", date_added=timezone.now()
        )

    def test_ip_address_creation(self):
        instance = self.ip_address

        self.assertTrue(isinstance(instance, ip_address))
        self.assertEqual(
            instance.__str__(),
            f"{instance.study} : {instance.ip_address} : {instance.date_added}",
        )
