import logging

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import (Administration, Demographic, Instrument,
                                  PaymentCode, Study, administration_data)
from researcher_UI.tests import generate_fake_results
from researcher_UI.utils.random_url_generator import random_url_generator

logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)


class AdministrationSummaryViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://example.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash=random_url_generator(),
            completed=False,
            due_date=timezone.now(),
        )

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse(
            "administration_summary_view",
            kwargs={"hash_id": self.administration.url_hash},
        )

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_completed_get(self):
        self.client.force_login(self.user)
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_completed_WG_get(self):
        self.client.force_login(self.user)
        instrument = Instrument.objects.get(
            language="English",
            form="WG",
        )
        study = Study.objects.create(
            researcher=self.user,
            name="WG Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )
        generate_fake_results(study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_redirect_boolean(self):
        self.study.redirect_boolean = True
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_indirect_redirect_boolean(self):
        self.study.redirect_boolean = True
        self.study.direct_redirect_boolean = False
        self.study.json_redirect = {
            "token": "DD266E7616FE86C190DEBC530CE5E435",
            "content": "surveyLink",
            "format": "json",
            "instrument": "webcdi",
            "event": "v01_arm_1",
            "record": "YISKL0001",
            "returnFormat": "json",
        }
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_backpage_demographic(self):
        demographic = Demographic.objects.get(name="English_Split.json")
        self.study.demographic = demographic
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_payment_amazon(self):
        self.study.allow_payment = True
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        payment_code = PaymentCode(
            study=self.study,
            payment_type="Amazon",
            gift_amount=25.00,
            gift_code="1234567890",
            hash_id=administration.url_hash,
        )
        payment_code.save()
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_payment_tango(self):
        self.study.allow_payment = True
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        payment_code = PaymentCode(
            study=self.study,
            payment_type="Tango",
            gift_amount=25.00,
            gift_code="1234567890",
            hash_id=administration.url_hash,
        )
        payment_code.save()
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_allow_payment_expired(self):
        self.study.allow_payment = True
        self.study.save()
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class AdministrationDetailViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

    def test_view_get(self):
        self.client.force_login(self.user)
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse("administration-view", kwargs={"pk": administration.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class AdministrationUpdateViewTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now(),
        )

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse(
            "update_administration", kwargs={"hash_id": self.administration.url_hash}
        )

    def test_get(self):
        self.client.force_login(self.user)
        self.administration.page_number = 1
        self.administration.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_previous_get(self):
        self.client.force_login(self.user)
        self.administration.page_number = 10
        self.administration.save()
        url = reverse(
            "update_administration_section_previous",
            kwargs={
                "hash_id": self.administration.url_hash,
                "section": 1,
                "previous": True,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_completed_get(self):
        self.client.force_login(self.user)
        self.administration.completed = True
        self.administration.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_completed_post(self):
        self.client.force_login(self.user)
        self.administration.completed = True
        self.administration.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_btn_save_post(self):
        self.client.force_login(self.user)
        payload = {"btn-save": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_previous_post(self):
        self.client.force_login(self.user)

        payload = {"btn-previous": True, "previous": 10}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_next_post(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 12}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    @tag('new')
    def test_post_enabler_blank(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30}
        url = reverse(
            "update_administration_section", kwargs={"hash_id": self.administration.url_hash, 'section': 29}
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section", kwargs={"hash_id": self.administration.url_hash, 'section': 30}
        )
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        response = self.client.get(redirect_url, payload)
        self.assertContains(response, "Thank you for completing!")

    @tag('new')
    def test_post_enabler_negative(self):
        self.client.force_login(self.user)

        payload = {
            "btn-next": True, 
            "next": 30,
            "item_760": "not yet"}
        url = reverse(
            "update_administration_section", kwargs={"hash_id": self.administration.url_hash, 'section': 29}
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section", kwargs={"hash_id": self.administration.url_hash, 'section': 30}
        )
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        response = self.client.get(redirect_url, payload)
        self.assertContains(response, "Thank you for completing!")

    @tag('new')
    def test_post_enabler_sometimes(self):
        self.client.force_login(self.user)

        payload = {
            "btn-next": True, 
            "next": 30,
            "item_760": "sometimes"}
        url = reverse(
            "update_administration_section", kwargs={"hash_id": self.administration.url_hash, 'section': 29}
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section", kwargs={"hash_id": self.administration.url_hash, 'section': 30}
        )
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        response = self.client.get(redirect_url, payload)
        self.assertNotContains(response, "Thank you for completing!")

    @tag('new')
    def test_post_enabler_often(self):
        self.client.force_login(self.user)

        payload = {
            "btn-next": True, 
            "next": 30,
            "item_760": "often"}
        url = reverse(
            "update_administration_section", kwargs={"hash_id": self.administration.url_hash, 'section': 29}
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section", kwargs={"hash_id": self.administration.url_hash, 'section': 30}
        )
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        response = self.client.get(redirect_url, payload)
        self.assertNotContains(response, "Thank you for completing!")

    def test_btn_back_post(self):
        self.client.force_login(self.user)
        payload = {"btn-back": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_submit_post(self):
        self.client.force_login(self.user)
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_submit_allow_payment_post(self):
        self.client.force_login(self.user)
        self.study.allow_payment = True
        self.study.save()
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_btn_submit_with_payment_post(self):
        payment_code = PaymentCode(
            study=self.study,
            payment_type="Amazon",
            gift_amount=25.00,
            gift_code="1234567890",
        )
        payment_code.save()
        self.client.force_login(self.user)
        self.study.allow_payment = True
        self.study.name = "Wordful Study (Official)"
        self.study.save()
        self.administration.repeat_num = 2
        self.administration.save()
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        pc = PaymentCode.objects.get(gift_code="1234567890")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pc.hash_id, self.administration.url_hash)

    def test_backpage_post(self):
        demographic = Demographic.objects.get(name="English_Split.json")
        self.study.demographic = demographic
        self.study.save()
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_page_in_item_type_post(self):
        for instrument in Instrument.objects.exclude(form="CAT"):
            study = Study(
                researcher=self.user,
                name=f"{instrument.name} Test Study Instance",
                instrument=instrument,
                redirect_url="https://redirect_url.com/redirect/{source_id}",
            )
            study.save()
            administration = Administration.objects.create(
                study=study,
                subject_id=1,
                repeat_num=1,
                url_hash=random_url_generator(),
                completed=False,
                due_date=timezone.now(),
            )
            administration.save()

            payload = {"btn-next": True, "next": 12}
            url = reverse(
                "update_administration", kwargs={"hash_id": administration.url_hash}
            )

            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 302)

    def test_completion_data(self):
        self.study.no_demographic_boolean = True
        self.study.completion_data = {
            "record_id": "{{source_id}}",
            "redcap_event_name": "{{event_id}}",
            "webcdi_completion_status": "1",
        }
        self.study.send_completion_flag_url = "https://example.com"
        self.study.save()
        payload = {"btn-submit": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_post_data(self):
        payload = {
            "btn-submit": True,
            "item_1": "produces",
            "item_2": "produces",
            "item_5": "no",
            "item_6": "no",
            "item_example1": "Example",
        }
        response = self.client.post(self.url, payload)
        administration_datas = administration_data.objects.filter(
            administration=self.administration
        ).count()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(3, administration_datas)
        example = administration_datas = administration_data.objects.get(
            administration=self.administration, item_ID="item_example1"
        )
        self.assertEqual(example.value, "Example")


class UpdateAdministrationDataItemTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="English",
            form="WS",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now(),
        )

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        self.url = reverse("update-administration-data-item")

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_upload_data(self):
        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_1",
            "value": "produces",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.get(
            administration=self.administration, item_ID="item_1"
        )
        self.assertEqual(item.value, "produces")

    def test_upload_data_removal(self):
        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_1",
            "value": "produces",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.get(
            administration=self.administration, item_ID="item_1"
        )
        self.assertEqual(item.value, "produces")

        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_1",
            "value": "",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.filter(
            administration=self.administration, item_ID="item_1"
        ).exists()
        self.assertEqual(item, False)

    def test_upload_data_change(self):
        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_761",
            "value": "simple",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.get(
            administration=self.administration, item_ID="item_761"
        )
        self.assertEqual(item.value, "simple")

        payload = {
            "hash_id": self.administration.url_hash,
            "check": "true",
            "item": "item_761",
            "value": "complex",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        item = administration_data.objects.get(
            administration=self.administration, item_ID="item_761"
        )
        self.assertEqual(item.value, "complex")
