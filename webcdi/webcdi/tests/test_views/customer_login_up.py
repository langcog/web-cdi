import logging

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from brookes.models import BrookesCode
from researcher_UI.models import Instrument, InstrumentFamily, Researcher
from webcdi.views import CustomLoginView

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class CustomLoginViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="henry", password="secret")
        Researcher.objects.get_or_create(user=self.user)
        instrument_family = InstrumentFamily.objects.create(
            name="BigCats", chargeable=False
        )
        instrument = Instrument.objects.create(
            name="lion",
            language="lionish",
            form="roar",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        self.user.researcher.allowed_instruments.add(instrument)
        self.user.researcher.allowed_instrument_families.add(instrument_family)

        self.user.researcher.save()
        self.screen = CustomLoginView
        self.url = reverse("login")

        self.valid_payload = {"username": "henry", "password": "secret"}

        self.invalid_payload = {"username": "henry", "password": "not-a-secret"}

        self.code = BrookesCode.objects.create(
            researcher=self.user,
            instrument_family=instrument_family,
            applied=timezone.now() - relativedelta(days=350),
            expiry=timezone.now() + relativedelta(days=15),
        )

    def test_webcdi_custom_login_get(self):
        request = RequestFactory().get(self.url)
        request.user = self.user
        response = self.screen.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_webcdi_custom_login_post_isInValid(self):
        response = self.client.post(self.url, self.invalid_payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Please enter a correct username and password. Note that both fields may be case-sensitive.",
            status_code=200,
        )

    def test_webcdi_custom_login_post_isValid(self):
        response = self.client.post(self.url, self.valid_payload)
        self.assertRedirects(response, "/accounts/profile/", target_status_code=302)
        self.assertEqual(response.status_code, 302)

    def test_webcdi_custom_login_old_brookes_code_post_isValid(self):
        response = self.client.post(self.url, self.valid_payload)
        self.assertRedirects(response, "/accounts/profile/", target_status_code=302)
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            f"Your licence for {self.code.instrument_family} will expire on {self.code.expiry}",
        )
