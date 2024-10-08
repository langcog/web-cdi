import logging

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Researcher, Study)
from researcher_UI.tests.utils import random_password
from researcher_UI.views import EditAdministrationView, StudyFormForm

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class EditAdministrationViewTest(TestCase):
    def setUp(self):
        self.password = random_password()
        self.user = User.objects.create_user(
            username="test_user", password=self.password
        )
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

        study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now(),
        )
        self.user.researcher.allowed_instruments.add(instrument)
        self.user.researcher.allowed_instrument_families.add(instrument_family)
        self.user.researcher.save()

        self.screen = EditAdministrationView
        self.url = reverse(
            "researcher_ui:edit_study_new", kwargs={"pk": self.administration.id}
        )

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_isInvalid(self):
        self.client.force_login(self.user)
        payload = {
            "id": self.administration.id,
            "subject_id": self.administration.subject_id,
            "local_lab_id": "abc",
            "opt_out": "peanut",
        }
        form = StudyFormForm(data=payload)
        self.assertEqual(form.errors["subject_id_old"][0], "This field is required.")

    def test_post_isValid(self):
        self.client.force_login(self.user)
        payload = {
            "id": self.administration.id,
            "subject_id": self.administration.subject_id + 1,
            "local_lab_id": "abc",
            "opt_out": True,
            "subject_id_old": self.administration.subject_id,
        }
        form = StudyFormForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"], "Your data is updated successfully"
        )


class AddNewParentTest(TestCase):
    def setUp(self):
        self.username = "study_user"
        self.password = random_password()
        self.user = User.objects.create_user(
            username="study_user", password=self.password
        )
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

        study = Study.objects.create(
            researcher=self.user,
            name="TestStudyInstance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now(),
        )
        self.user.researcher.allowed_instruments.add(instrument)
        self.user.researcher.allowed_instrument_families.add(instrument_family)
        self.user.researcher.save()

        self.screen = EditAdministrationView
        self.url = reverse(
            "researcher_ui:administer_new_parent",
            kwargs={"username": self.username, "study_name": study.name},
        )

    def test_get_isValid(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_pos_offset(self):
        self.administration.study.no_demographic_boolean = True
        self.administration.study.save()
        self.client.force_login(self.user)
        url = f"{self.url}?offset=2&source_id=123456&age=15&sex=m"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_neg_offset(self):
        self.administration.study.no_demographic_boolean = True
        self.administration.study.save()
        self.client.force_login(self.user)
        url = f"{self.url}?offset=-2&source_id=123456&age=15&sex=m"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_no_offset(self):
        self.administration.study.no_demographic_boolean = True
        self.administration.study.save()
        self.client.force_login(self.user)
        url = f"{self.url}?source_id=123456&age=15&sex=m"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_event_id(self):
        self.administration.study.no_demographic_boolean = True
        self.administration.study.save()
        self.client.force_login(self.user)
        url = f"{self.url}?source_id=123456&age=15&sex=m&event_id=test"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_repeat_num(self):
        self.administration.study.no_demographic_boolean = True
        self.administration.study.save()
        self.client.force_login(self.user)
        url = f"{self.url}?source_id=123456&age=15&sex=m&event_id=stage_1"
        response = self.client.get(url)
        administrations = Administration.objects.filter(
            backgroundinfo__source_id="123456"
        )
        self.assertEqual(1, len(administrations))
        self.assertEqual(response.status_code, 302)

        self.administration.study.no_demographic_boolean = True
        self.administration.study.save()
        self.client.force_login(self.user)
        url = f"{self.url}?source_id=123456&age=15&sex=m&event_id=stage_2"
        response = self.client.get(url)
        administrations = Administration.objects.filter(
            backgroundinfo__source_id="123456"
        )
        self.assertEqual(2, len(administrations))
        self.assertEqual(response.status_code, 302)

    def test_no_age(self):
        self.administration.study.no_demographic_boolean = True
        self.administration.study.save()
        self.client.force_login(self.user)
        url = f"{self.url}?source_id=123456&sex=m"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_no_set(self):
        self.administration.study.no_demographic_boolean = True
        self.administration.study.save()
        self.client.force_login(self.user)
        url = f"{self.url}?source_id=123456&age=15"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
