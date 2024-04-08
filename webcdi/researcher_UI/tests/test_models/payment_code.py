from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from researcher_UI.models import (Instrument, InstrumentFamily, PaymentCode,
                                  Study)

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
