from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from brookes.models import BrookesCode
from researcher_UI.models import InstrumentFamily


@tag("context_processor")
class BrookesContextProcessorTest(TestCase):
    def setUp(self):
        self.brookes_user = User.objects.create_user(
            username="brookes_user", password="secret"
        )

        self.not_brookes_user = User.objects.create_user(
            username="not_brookes", password="secret"
        )

        instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=True
        )
        BrookesCode.objects.create(
            researcher=self.brookes_user,
            applied=timezone.now() - relativedelta(months=1),
            expiry=timezone.now() + relativedelta(days=7),
            instrument_family=instrument_family,
        )
        instrument_family2 = InstrumentFamily.objects.create(
            name="Instrument Family 2 Test Model", chargeable=True
        )
        BrookesCode.objects.create(
            researcher=self.brookes_user,
            applied=timezone.now() - relativedelta(months=1),
            expiry=timezone.now() + relativedelta(months=11),
            instrument_family=instrument_family2,
        )

    def test_user_has_brookes_renewal_code(self):
        self.client.login(username=self.brookes_user.username, password="secret")
        response = self.client.get(reverse("researcher_ui:console"))
        self.assertIn("RENEWAL_CODES", response.context)
        self.assertEqual(len(response.context["RENEWAL_CODES"]), 1)

    def test_user_has_not_brookes_renewal_code(self):
        self.client.login(username=self.not_brookes_user.username, password="secret")
        response = self.client.get(reverse("researcher_ui:console"))
        self.assertIn("RENEWAL_CODES", response.context)
        self.assertEqual(len(response.context["RENEWAL_CODES"]), 0)

    def test_anon_user(self):
        response = self.client.get(reverse("researcher_ui:console"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/interface/")
