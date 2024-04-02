import logging

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from researcher_UI.forms import AddStudyForm
from researcher_UI.models import Instrument, Researcher, Study, InstrumentFamily
from researcher_UI.views import AddStudy, Console, AdminNew

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class NoUserRedirectTest(TestCase):
    url = reverse("researcher_ui:console")
    login_url = "/accounts/login/?next=/interface/"

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
        Researcher.objects.get_or_create(user=self.user)
        instrument_family, created = InstrumentFamily.objects.get_or_create(name='BigCats', chargeable=False)
        instrument, created = Instrument.objects.get_or_create(
            name="lion", language="lionish", form="roar", min_age=3, max_age=15, family=instrument_family
        )
        self.user.researcher.allowed_instruments.add(instrument)
        self.user.researcher.allowed_instrument_families.add(instrument_family)
        
        self.user.researcher.save()
        self.screen = AddStudy
        self.url = reverse("researcher_ui:add_study")
        self.invalid_payload = {
            "name": "TestStudy",
        }
        self.valid_payload = {"name": "TestStudy", "instrument": "lion", "researcher": self.user,
                              'prefilled_data': 0, 'birth_weight_units': 'lb', 
                              'timing': 6, 'participant_source_boolean': 0, 'end_message': 'standard', 
                              'gift_card_provider': 'Amazon'}

    def test_get(self):
        request = RequestFactory().get(self.url)
        request.user = self.user
        response = self.screen.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_post_isInvalid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.invalid_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['instrument'][0], 'This field is required.')
        self.assertIn("researcher", response.context)

    def test_post_isValid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertRedirects(response, "/interface/study/1/detail/")
        self.assertEqual(response.status_code, 302)

class AdminNewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="henry", password="poiuytre12")
        Researcher.objects.get_or_create(user=self.user)
        instrument_family, created = InstrumentFamily.objects.get_or_create(name='BigCats', chargeable=False)
        instrument, created = Instrument.objects.get_or_create(
            name="lion", language="lionish", form="roar", min_age=3, max_age=15, family=instrument_family
        )
        self.user.researcher.allowed_instruments.add(instrument)
        self.user.researcher.allowed_instrument_families.add(instrument_family)
        self.study, created = Study.objects.get_or_create(name='TestStudy', researcher=self.user, instrument=instrument)
        self.screen = AdminNew
        self.url = reverse("researcher_ui:administer_new", kwargs={'pk': self.study.pk})
        self.invalid_payload = {
            "name": "TestStudy",
        }
        self.valid_payload = {"new_subject_ids": [1, 2, 3], "autogenerate_count": ''}

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # TODO
    # Code needs changing to use form properly for this test
    def test_post_isInvalid(self):
        pass

    def test_post_isValid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, 200)