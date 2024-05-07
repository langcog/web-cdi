from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from researcher_UI.models import (Instrument, InstrumentFamily, PaymentCode,
                                  Study)
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model")
class PaymentCodeModelTest(TestCase):
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

        self.payment_code = PaymentCode.objects.create(
            study=study,
            hash_id="123456",
            added_date=timezone.now(),
            payment_type="Amazon",
            gift_amount=10.00,
            gift_code="GIFTCODE",
        )

    def test_payment_code_creation(self):
        instance = self.payment_code

        self.assertTrue(isinstance(instance, PaymentCode))
        self.assertEqual(instance.__str__(), f"{instance.study} {instance.gift_code}")

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = self.payment_code

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
