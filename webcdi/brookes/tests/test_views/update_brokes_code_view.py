import logging

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from brookes.models import BrookesCode
from researcher_UI.models import InstrumentFamily

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)

class UpdateBrookesCodeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="henry", password="secret")
        brookes_code = BrookesCode.objects.create()
        self.instrument_family = InstrumentFamily.objects.create(
            name="BigCats", chargeable=True
        )
        self.url = reverse(
            "brookes:enter_codes",
            kwargs={"instrument_family": self.instrument_family.id},
        )

        self.valid_payload = {
            "code": brookes_code.code,
        }
        self.cancel_payload = {"code": brookes_code.code, "cancel": "Cancel"}
        self.invalid_payload = {
            "code": "123456789012345",
        }

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_isInvalid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.invalid_payload)
        self.assertEqual(response.status_code, 200)

    def test_post_cancel(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.cancel_payload)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("researcher_ui:console"))

    def test_post_isValid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("researcher_ui:console"))

    def test_extending_brookes(self):
        now = timezone.now()
        BrookesCode.objects.create(
            researcher=self.user,
            instrument_family=self.instrument_family,
            applied=now - relativedelta(years=1),
            expiry=now + relativedelta(days=7),
        )
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("researcher_ui:console"))
        bc = BrookesCode.objects.get(code=self.valid_payload["code"])
        self.assertEqual(
            bc.expiry, now + relativedelta(days=7) + relativedelta(years=1)
        )
