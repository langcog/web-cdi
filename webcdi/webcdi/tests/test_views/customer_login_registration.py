import logging

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from brookes.models import BrookesCode
from researcher_UI.models import Instrument, InstrumentFamily, Researcher
from researcher_UI.tests.utils import random_password
from webcdi.views import CustomLoginView, CustomRegistrationView

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class CustomLoginViewTest(TestCase):

    def setUp(self):
        self.password = random_password()
        self.not_a_password = random_password()
        self.user = User.objects.create_user(username="henry", password=self.password)
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

        self.valid_payload = {"username": "henry", "password": self.password}

        self.invalid_payload = {"username": "henry", "password": self.not_a_password}

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


@tag("new")
class CustomRegistrationViewTest(TestCase):

    def setUp(self):
        password = random_password()
        self.username = "TestUser"
        self.institution = "Test Institution"
        self.position = "Test Position"
        self.first_name = "FirstNameTest"
        self.last_name = "LastNameTest"

        self.valid_payload = {
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": "test.user@example.com",
            "institution": self.institution,
            "position": self.position,
            "password1": password,
            "password2": password,
        }

        self.invalid_payload = {"username": "henry", "password": "not-a-secret"}

        self.screen = CustomRegistrationView
        self.url = reverse("django_registration_register")

    def test_webcdi_custom_registration_get(self):
        request = RequestFactory().get(self.url)
        response = self.screen.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_webcdi_custom_registration_post_isInValid(self):
        response = self.client.post(self.url, self.invalid_payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This field is required.",
            status_code=200,
        )

    def test_webcdi_custom_registration_post_isValid(self):
        response = self.client.post(self.url, self.valid_payload)
        self.assertRedirects(
            response,
            "/accounts/register/complete/",
            status_code=302,
            target_status_code=200,
        )
        self.assertEqual(response.status_code, 302)

        researcher = Researcher.objects.get(
            user=User.objects.get(username=self.username)
        )
        self.assertEqual(
            researcher.__str__(),
            f"{self.first_name} {self.last_name} ({self.position}, {self.institution})",
        )
