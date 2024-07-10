from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase, tag
from django.urls import reverse

from researcher_UI.forms import AddInstrumentForm
from researcher_UI.models import Instrument, Study


class AddInstrumentsTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):

        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        self.instrument = Instrument.objects.filter(
            language="English",
            form="WS",
        )[0]

        self.study = Study.objects.create(
            researcher=self.user,
            instrument=self.instrument,
            min_age=self.instrument.min_age,
            max_age=self.instrument.max_age,
            name="Test Instrument 1",
        )

    @tag("new")
    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "researcher_ui:researcher_add_instruments", kwargs={"pk": self.user.id}
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.force_login(self.user)
        payload = {"id_allowed_instrument_families_0": True}
        response = self.client.post(
            reverse(
                "researcher_ui:researcher_add_instruments", kwargs={"pk": self.user.id}
            ),
            payload,
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("researcher_ui:console"))

    def test_post_brookes(self):
        # TODO
        pass
