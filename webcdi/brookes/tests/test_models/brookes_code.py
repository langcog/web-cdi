from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from brookes.models import BrookesCode
from researcher_UI.models import InstrumentFamily

# models test


@tag("model")
class BrookesCodeModelTest(TestCase):
    def setUp(self) -> None:

        self.brookes_code = BrookesCode.objects.create()

        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        self.instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=True
        )

    def test_brookes_code_creation(self):
        instance = self.brookes_code

        self.assertTrue(isinstance(instance, BrookesCode))
        self.assertEqual(instance.__str__(), f"{instance.code}")

    def test_brookes_code_expiry_set(self):
        instance = self.brookes_code
        instance.researcher = self.user
        instance.instrument_family = self.instrument_family
        now = timezone.now()
        instance.applied = now
        instance.save()
        expiry = now + relativedelta(years=1)

        self.assertTrue(isinstance(instance, BrookesCode))
        self.assertEqual(instance.__str__(), f"{instance.code}")
        self.assertEqual(instance.expiry, expiry)
