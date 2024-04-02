import logging

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from researcher_UI.models import Instrument
from researcher_UI.views import AddStudy, Console

logger = logging.getLogger("selenium")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)


class NoUserRedirectTest(TestCase):
    url = reverse("researcher_ui:console")
    login_url = "/accounts/login/?next=/interface/"
    client = Client()

    def test_http_status_code_302(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            self.login_url,
        )


class LoginTestCase(TestCase):
    def setUp(self):
        User.objects.create(username="henry", password="poiuytre12")

    def test_user_can_login(self):
        c = Client()
        response = c.post(
            "/accounts/login/", {"username": "henry", "password": "poiuytre12"}
        )
        self.assertEqual(200, response.status_code)


class ConsoleViewTest(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = User.objects.create_user(username="henry", password="poiuytre12")

    def test_studies_set_in_context(self):
        request = RequestFactory().get(reverse("researcher_ui:console"))
        request.user = self.user
        view = Console()
        view.setup(request)
        context = view.get_context_data()
        self.assertIn("studies", context)


class AddStudyViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="henry", password="poiuytre12")
        self.screen = AddStudy
        self.url = reverse("researcher_ui:add_study")
        self.payload = {
            "name": "TestStudy",
        }

    def test_context(self):
        request = RequestFactory().get(self.url)
        request.user = self.user
        view = AddStudy()
        view.setup(request)
        context = view.get_context_data()
        self.assertIn("researcher", context)

    def test_get(self):
        request = RequestFactory().get(self.url)
        request.user = self.user
        response = self.screen.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_post_form_isInvalid(self):
        request = RequestFactory().post(self.url, self.payload)
        request.user = self.user
        response = self.screen.as_view()(request)
        self.assertEqual(response.status_code, 200)

        c = Client()
        response = c.post(self.url, self.payload)
        self.assertRedirects(response, "/accounts/login/?next=/interface/study/add/")

    def test_post_form_isValid(self):
        request = RequestFactory().post(self.url, self.payload)
        request.user = self.user
        response = self.screen.as_view()(request)
        self.assertEqual(response.status_code, 200)
