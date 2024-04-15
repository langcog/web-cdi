from django.contrib.auth.models import User
from django.test import TestCase, tag

from brookes.views import *


@tag("url")
class TestBrookesUrls(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        self.instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=True
        )

    def test_enter_codes_url(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "brookes:enter_codes",
                kwargs={"instrument_family": self.instrument_family.id},
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_brookes_redirect_enter_codes(self):
        response = self.client.get(
            reverse(
                "brookes:enter_codes",
                kwargs={"instrument_family": self.instrument_family.id},
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("brookes:enter_codes", kwargs={"instrument_family": self.instrument_family.id},)}',
        )
