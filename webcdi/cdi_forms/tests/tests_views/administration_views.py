import datetime
import logging

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
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

    def test_jquery_loads_before_bootstrap(self):
        # staging QA: "Show Me My Answers" did nothing because Bootstrap's JS
        # (which wires up the collapse toggle) ran before jQuery existed
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(completed=True)[0]
        url = reverse(
            "administration_summary_view", kwargs={"hash_id": administration.url_hash}
        )
        page = self.client.get(url).content.decode()
        self.assertIn("Show Me My Answers", page)  # the summary page, not "expired"
        self.assertLess(page.index("jquery-3.7.1.min.js"), page.index("bootstrap/bootstrap.min.js"))

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
        # this study's own administration (fixture administrations may already have codes)
        administration = Administration.objects.filter(
            study=self.study, completed=True
        )[0]
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
        # this study's own administration (fixture administrations may already have codes)
        administration = Administration.objects.filter(
            study=self.study, completed=True
        )[0]
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

    def test_post_enabler_blank(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30}
        url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 29},
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 30},
        )
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        response = self.client.get(redirect_url, payload)
        self.assertContains(response, "Thank you for completing!")

    def test_post_enabler_negative(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30, "item_760": "not yet"}
        url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 29},
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 30},
        )
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        response = self.client.get(redirect_url, payload)
        self.assertContains(response, "Thank you for completing!")

    def test_post_enabler_sometimes(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30, "item_760": "sometimes"}
        url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 29},
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 30},
        )
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        response = self.client.get(redirect_url, payload)
        self.assertNotContains(response, "Thank you for completing!")

    def test_post_enabler_often(self):
        self.client.force_login(self.user)

        payload = {"btn-next": True, "next": 30, "item_760": "often"}
        url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 29},
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        redirect_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 30},
        )
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        response = self.client.get(redirect_url, payload)
        self.assertNotContains(response, "Thank you for completing!")

    def test_btn_back_post(self):
        self.client.force_login(self.user)
        payload = {"btn-back": True}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)

    def test_back_to_background_returns_to_same_section(self):
        # "Go back to Background Info" from section 3, then "Next" on the
        # background page, should land the parent on section 3 again (not 4).
        self.study.min_age = 12
        self.study.max_age = 36
        self.study.save()
        self.administration.due_date = timezone.now() + datetime.timedelta(days=14)
        self.administration.completedBackgroundInfo = True
        self.administration.save()
        section_url = reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": 3},
        )

        response = self.client.post(section_url, {"btn-back": True})
        self.assertEqual(response.status_code, 302)
        background_url = response.url
        self.assertTrue(
            background_url.startswith(
                reverse(
                    "background-info",
                    args=(self.administration.backgroundinfo.pk,),
                )
            )
        )

        dob = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime(
            "%m/%d/%Y"
        )
        payload = {
            "btn-next": "Next",
            "form_filler": "mother",
            "child_dob": dob,
            "sex": "M",
            "birth_weight_lb": "3.5",
            "birth_order": 1,
            "born_on_due_date": 0,
            "multi_birth_boolean": 0,
            "primary_caregiver": "mother",
            "mother_yob": 1966,
            "mother_education": 18,
            "annual_income": "25000-50000",
            "caregiver_info": "1",
            "other_languages_boolean": 0,
            "ear_infections_boolean": 0,
            "hearing_loss_boolean": 0,
            "vision_problems_boolean": 0,
            "illnesses_boolean": 0,
            "services_boolean": 0,
            "worried_boolean": 0,
            "learning_disability_boolean": 0,
        }
        response = self.client.post(background_url, payload, follow=True)
        self.assertEqual(response.redirect_chain[-1][0], section_url)

    def resume_url(self):
        """Where reopening the parent's link sends them."""
        response = self.client.get(
            reverse("administer_cdi_form", args=(self.administration.url_hash,))
        )
        return response.url

    def section_url(self, section):
        return reverse(
            "update_administration_section",
            kwargs={"hash_id": self.administration.url_hash, "section": section},
        )

    def test_resume_where_the_parent_was_sent(self):
        self.administration.due_date = timezone.now() + datetime.timedelta(days=14)
        self.administration.completedBackgroundInfo = True
        self.administration.save()
        for button, payload, resume_at in [
            ("save", {"btn-save": True}, 4),
            ("next", {"btn-next": True, "next": 5}, 5),
            ("previous", {"btn-previous": True, "previous": 3}, 3),
        ]:
            with self.subTest(button=button):
                self.client.post(self.section_url(4), payload)
                self.assertEqual(self.resume_url(), self.section_url(resume_at))

    def test_section_past_the_end_shows_the_last_section(self):
        # English WS has sections 1-31
        last = self.client.get(self.section_url(31)).context["data"]["menu"]
        response = self.client.get(self.section_url(99))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["data"]["menu"], last)

    def test_page_without_section_resumes_from_page_number(self):
        self.administration.page_number = 6
        self.administration.save()
        self.assertEqual(self.client.get(self.url).context["data"]["menu"], 6)
        self.administration.page_number = 0
        self.administration.save()
        self.assertEqual(self.client.get(self.url).context["data"]["menu"], 1)

    def test_migration_keeps_in_progress_parents_where_they_were(self):
        import importlib

        from django.apps import apps

        migration = importlib.import_module(
            "researcher_UI.migrations.0108_page_number_is_resume_section"
        )
        self.administration.page_number = 4  # old meaning: last posted from 4
        self.administration.save()
        done = Administration.objects.create(
            study=self.study, subject_id=2, repeat_num=1, url_hash="d" * 64,
            completed=True, due_date=timezone.now(), page_number=4,
        )
        migration.forwards(apps, None)
        self.administration.refresh_from_db()
        done.refresh_from_db()
        self.assertEqual(self.administration.page_number, 5)  # old code resumed at 4 + 1
        self.assertEqual(done.page_number, 4)

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

    def test_missing_params(self):
        # #630: used to raise MultiValueDictKeyError (500)
        base = {"hash_id": self.administration.url_hash}
        for payload in [
            {**base, "item": "item_1", "value": "produces"},  # no check
            {**base, "check": "true", "value": "produces"},  # no item
            {**base, "check": "true", "item": "item_1"},  # no value
        ]:
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, 400, payload)
        self.assertFalse(
            administration_data.objects.filter(
                administration=self.administration
            ).exists()
        )

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


class UpdateSummaryViewTest(TestCase):
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

    def test_completed_get(self):
        self.client.force_login(self.user)
        generate_fake_results(self.study, 10)
        args = []
        opts = {}
        call_command("update_summary_data", *args, **opts)
        self.assertEquals(
            10, Administration.objects.filter(study=self.study, scored=True).count()
        )
        # progress goes to the log, not to anyone's inbox
        self.assertEqual(len(mail.outbox), 0)
