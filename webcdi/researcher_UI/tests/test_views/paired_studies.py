
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from researcher_UI.forms import AddPairedStudyForm
from researcher_UI.models import (
    Instrument,
    Researcher,
    Study,
)
from researcher_UI.tests import generate_fake_results
from researcher_UI.tests.utils import random_password


class PairedStudyCreateViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self) -> None:
        super().setUp()
        self.password = random_password()
        self.user = User.objects.create_user(
            username="test_user", password=self.password
        )
        Researcher.objects.get_or_create(user=self.user)

        for counter in range(3):
            instrument = Instrument.objects.filter(form="WS").order_by("?")[0]
            study = Study.objects.create(
                researcher=self.user,
                name=f"Study {counter}",
                instrument=instrument,
                max_age=instrument.max_age,
                min_age=instrument.min_age,
            )
            generate_fake_results(study, 20)

        studies = Study.objects.filter(researcher=self.user).order_by("?")
        self.study = studies[0]
        self.study1 = studies[1]

        self.url = reverse("researcher_ui:add_paired_study")
        self.delete_url = reverse(
            "researcher_ui:console_study", kwargs={"pk": self.study1.pk}
        )

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # TODO this test doesn't work
    def test_AddPairedStudyForm(self):
        self.client.force_login(self.user)
        request = RequestFactory().get(reverse("researcher_ui:console"))
        request.user = self.user

        study_group = "StudyGroup"
        payload = {
            "study_group": study_group,
            "paired_studies": [self.study.id, self.study1.id],
            "request": request,
        }
        form = AddPairedStudyForm(data=payload)
        self.assertTrue(form.is_valid())

    # TODO this test doesn't work
    def test_failed_AddPairedStudyForm(self):
        self.client.force_login(self.user)
        request = RequestFactory().get(reverse("researcher_ui:console"))
        request.user = self.user

        study_group = "StudyGroup"
        payload = {"study_group": study_group, "paired_studies": [], "request": request}
        form = AddPairedStudyForm(data=payload)
        self.assertTrue(form.is_valid())

    def test_post(self):
        self.client.force_login(self.user)
        study_group = "StudyGroup"
        payload = {
            "study_group": study_group,
            "paired_studies": [self.study.id, self.study1.id],
        }
        response = self.client.post(self.url, payload)
        self.assertRedirects(response, reverse("researcher_ui:console"))
        study = Study.objects.get(id=self.study.id)
        study1 = Study.objects.get(id=self.study1.id)
        self.assertEqual(study.study_group, study_group)
        self.assertEqual(study1.study_group, study_group)
