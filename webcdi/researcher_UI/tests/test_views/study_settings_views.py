import logging

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase, tag
from django.urls import reverse

from researcher_UI.forms import AddPairedStudyForm, EditStudyForm
from researcher_UI.models import (Instrument, InstrumentFamily, PaymentCode,
                                  Researcher, Study)
from researcher_UI.tests import generate_fake_results
from researcher_UI.tests.utils import random_password
from researcher_UI.views import AddStudy

logger = logging.getLogger("debug")


class AddStudyViewTest(TestCase):
    def setUp(self):
        self.password = random_password()
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
        self.screen = AddStudy
        self.url = reverse("researcher_ui:add_study")
        self.invalid_payload = {
            "name": "TestStudy",
        }
        self.valid_payload = {
            "name": "TestStudy",
            "instrument": "lion",
            "researcher": self.user,
            "prefilled_data": 0,
            "birth_weight_units": "lb",
            "timing": 6,
            "participant_source_boolean": 0,
            "end_message": "standard",
            "gift_card_provider": "Amazon",
        }

    def test_get(self):
        request = RequestFactory().get(self.url)
        request.user = self.user
        response = self.screen.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_post_isInvalid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.invalid_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors["instrument"][0], "This field is required."
        )
        self.assertIn("researcher", response.context)

    def test_post_isValid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, 302)


class AddPairedStudyTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self) -> None:
        super().setUp()
        self.password = random_password()
        self.user = User.objects.create_user(username="henry", password=self.password)
        Researcher.objects.get_or_create(user=self.user)

        for counter in range(3):
            instrument = Instrument.objects.all().order_by("?")[0]
            study = Study.objects.create(
                researcher=self.user,
                name=f"Study {counter}",
                instrument=instrument,
                max_age=instrument.max_age,
                min_age=instrument.min_age,
            )
            generate_fake_results(study, 10)

        self.study = Study.objects.filter(researcher=self.user).order_by("?")[0]

        self.url = reverse("researcher_ui:add_paired_study")

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.force_login(self.user)
        payload = {"study_group": "StudyGroup", "paired_studies": [self.study.id]}
        form = AddPairedStudyForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)


class UpdateStudyTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self) -> None:
        super().setUp()
        self.password = random_password()
        self.user = User.objects.create_user(username="henry", password=self.password)
        Researcher.objects.get_or_create(user=self.user)

        family = InstrumentFamily.objects.get(name="English (American) Short")
        instrument = Instrument.objects.get(
            language="English", family=family, form="L1"
        )
        self.user.researcher.allowed_instruments.add(instrument)
        self.user.researcher.allowed_instrument_families.add(family)

        self.study_name = "Test Study"
        self.study = Study(
            name=self.study_name, instrument=instrument, researcher=self.user
        )
        self.study.save()

        generate_fake_results(self.study, 10)

        self.new_name = "New Study Name"
        self.non_chargeable_payload = {
            "name": self.new_name,
            "instrument": instrument.name,
            "researcher": self.user,
            "prefilled_data": 0,
            "birth_weight_units": "lb",
            "timing": 6,
            "participant_source_boolean": 0,
            "end_message": "standard",
            "gift_card_provider": "Amazon",
            "test_period": 14,
        }

        self.url = reverse("researcher_ui:rename_study", kwargs={"pk": self.study.pk})

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_non_chargeable(self):
        self.client.force_login(self.user)

        form = EditStudyForm(data=self.non_chargeable_payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, self.non_chargeable_payload)
        self.assertRedirects(
            response,
            reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk}),
        )  # , status_code=200, target_status_code=302)

    def test_post_vouchers_amazon(self):
        self.client.force_login(self.user)
        payload = self.non_chargeable_payload
        payload["gift_codes"] = ["1234-123456-1234, 1234-123456-1235"]
        payload["gift_amount"] = 10.00
        form = EditStudyForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        self.assertRedirects(
            response,
            reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk}),
        )  # , status_code=200, target_status_code=302)
        payment_codes = PaymentCode.objects.all()
        self.assertEqual(len(payment_codes), 2)

    def test_post_vouchers_tango(self):
        self.client.force_login(self.user)
        payload = self.non_chargeable_payload
        payload["gift_card_provider"] = "Tango"
        payload["gift_codes"] = (
            "www.rewardlink.io/r/1/QWERTYUIOPLKJHGFDSAZXCVBNMPOIUYTREWQASDFGHJ, www.rewardlink.io/r/1/QWERTYUIOPLKJHGFDSAZXCVBNMPOIUYTREWQASDFGHK"
        )
        payload["gift_amount"] = 10.00
        form = EditStudyForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        self.assertRedirects(
            response,
            reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk}),
        )  # , status_code=200, target_status_code=302)
        payment_codes = PaymentCode.objects.all()
        self.assertEqual(len(payment_codes), 2)

    def test_post_vouchers_invalid_code(self):
        self.client.force_login(self.user)
        payload = self.non_chargeable_payload
        payload["gift_card_provider"] = "Tango"
        payload["gift_codes"] = (
            "www.rewardlink.io/r/1/QWERTYUIOPLKJHGFDSAZXCVBNMPOIUYTRWQASDFGHJ"
        )
        payload["gift_amount"] = 10.00
        form = EditStudyForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0],
            "The following codes are invalid: ['www.rewardlink.io/r/1/QWERTYUIOPLKJHGFDSAZXCVBNMPOIUYTRWQASDFGHJ'].",
        )

    def test_post_vouchers_previously_added(self):
        self.client.force_login(self.user)
        payload = self.non_chargeable_payload
        payload["gift_codes"] = ["1234-123456-4321"]
        payload["gift_amount"] = 10.00
        form = EditStudyForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0], "The following codes have been added: ['1234-123456-4321']"
        )

        response = self.client.post(self.url, payload)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertEqual(len(messages), 2)
        self.assertEqual(
            messages[1], "The following codes are previously used: ['1234-123456-4321']"
        )

        self.assertRedirects(
            response,
            reverse("researcher_ui:console_study", kwargs={"pk": self.study.pk}),
        )  # , status_code=200, target_status_code=302)
        payment_codes = PaymentCode.objects.all()
        self.assertEqual(len(payment_codes), 1)

    def test_post_vouchers_invalid_amount(self):
        self.client.force_login(self.user)
        payload = self.non_chargeable_payload
        payload["gift_card_provider"] = "Tango"
        payload["gift_codes"] = (
            "www.rewardlink.io/r/1/QWERTYUIOPLKJHGFDSAZXCVBNMPOIUYTREWQASDFGHJ"
        )
        payload["gift_amount"] = 10, 00
        form = EditStudyForm(data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(self.url, payload)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], "The amount 0 is invalid")
