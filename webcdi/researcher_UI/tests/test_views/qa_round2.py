import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import (Administration, Instrument, PaymentCode,
                                  Researcher, Study)
from researcher_UI.utils.random_url_generator import random_url_generator


class GroupSettingsTestCase(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user("settings", password="x-test-only")
        Researcher.objects.get_or_create(user=self.user)
        self.instrument = Instrument.objects.get(language="Dutch", form="WS")
        self.user.researcher.allowed_instruments.add(self.instrument)
        self.study = Study.objects.create(
            researcher=self.user, name="First group", instrument=self.instrument
        )
        self.client.force_login(self.user)

    def payload(self, **kwargs):
        payload = {
            "name": "First group",
            "instrument": self.instrument.pk,
            "prefilled_data": 0,
            "birth_weight_units": "lb",
            "timing": 6,
            "participant_source_boolean": 0,
            "end_message": "standard",
            "gift_card_provider": "Amazon",
            "test_period": 14,
        }
        payload.update(kwargs)
        return payload

    def rename(self, name, **kwargs):
        return self.client.post(
            reverse("researcher_ui:rename_study", args=[self.study.pk]),
            self.payload(name=name, **kwargs),
        )


class GroupNameTest(GroupSettingsTestCase):
    def test_renaming_to_a_name_in_use_says_so(self):
        Study.objects.create(
            researcher=self.user, name="Second group", instrument=self.instrument
        )
        response = self.rename("Second group")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors["name"],
            ["Group names must be unique. You have already used 'Second group'."],
        )
        self.study.refresh_from_db()
        self.assertEqual(self.study.name, "First group")

    def test_renaming_to_a_deleted_groups_name_says_it_was_deleted(self):
        Study.objects.create(
            researcher=self.user,
            name="Old group",
            instrument=self.instrument,
            active=False,
        )
        response = self.rename("Old group")
        self.assertEqual(response.status_code, 200)
        self.assertIn("a group you deleted", response.context["form"].errors["name"][0])
        self.assertIn("webcdi-contact@stanford.edu", response.content.decode())

    def test_keeping_the_groups_own_name_saves(self):
        response = self.rename("First group", timing=8)
        self.assertEqual(response.status_code, 302)
        self.study.refresh_from_db()
        self.assertEqual(self.study.timing, 8)

    def test_another_researchers_name_is_free(self):
        other = User.objects.create_user("other", password="x-test-only")
        Study.objects.create(
            researcher=other, name="Shared name", instrument=self.instrument
        )
        self.assertEqual(self.rename("Shared name").status_code, 302)

    def test_a_new_group_with_a_deleted_groups_name_says_it_was_deleted(self):
        Study.objects.filter(pk=self.study.pk).update(active=False)
        response = self.client.post(reverse("researcher_ui:add_study"), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertIn("a group you deleted", response.context["form"].errors["name"][0])


class GroupNumberFieldsTest(GroupSettingsTestCase):
    def test_minimum_time_cannot_be_negative(self):
        response = self.rename("First group", timing=-5)
        self.assertEqual(response.status_code, 200)
        self.assertIn("timing", response.context["form"].errors)
        self.study.refresh_from_db()
        self.assertEqual(self.study.timing, 6)

    def test_minimum_time_of_zero_means_none(self):
        self.assertEqual(self.rename("First group", timing=0).status_code, 302)
        self.study.refresh_from_db()
        self.assertEqual(self.study.timing, 0)

    def test_gift_amount_cannot_be_negative(self):
        response = self.rename(
            "First group", gift_codes="1234-123456-1234", gift_amount="-5"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("gift_amount", response.context["form"].errors)
        self.assertFalse(PaymentCode.objects.filter(study=self.study).exists())


class GroupTableOrderTest(GroupSettingsTestCase):
    def make_rows(self, *keys):
        for subject_id, repeat_num in keys:
            Administration.objects.create(
                study=self.study,
                subject_id=subject_id,
                repeat_num=repeat_num,
                url_hash=random_url_generator(),
                completed=False,
                due_date=timezone.now() + datetime.timedelta(days=14),
            )

    def table_rows(self, **params):
        response = self.client.get(
            reverse("researcher_ui:console_study", args=[self.study.pk]), params
        )
        return [
            (row.record.subject_id, row.record.repeat_num)
            for row in response.context["study_administrations"].rows
        ]

    def test_rows_are_in_participant_order_whatever_order_they_were_made(self):
        self.make_rows((3, 1), (1, 2), (2, 1), (1, 1))
        self.assertEqual(self.table_rows(), [(1, 1), (1, 2), (2, 1), (3, 1)])

    def test_column_sorting_still_wins(self):
        self.make_rows((1, 1), (2, 1), (3, 1))
        self.assertEqual(
            self.table_rows(sort="-subject_id"), [(3, 1), (2, 1), (1, 1)]
        )


class ExternalSourceTextTest(GroupSettingsTestCase):
    def modal(self):
        response = self.client.get(
            reverse("researcher_ui:administer_new", args=[self.study.pk])
        )
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_a_group_with_a_background_form_says_each_visit_is_new(self):
        Study.objects.filter(pk=self.study.pk).update(participant_source_boolean=1)
        page = self.modal()
        self.assertIn("opening the link again starts a new administration", page)
        self.assertIn("PROLIFIC_PID", page)
        self.assertNotIn("a different event_id creates a new administration", page)
        self.assertNotIn("reopens that administration", page)

    def test_a_no_demographic_group_keeps_the_reopen_rule(self):
        Study.objects.filter(pk=self.study.pk).update(
            participant_source_boolean=1, no_demographic_boolean=True
        )
        page = self.modal()
        self.assertIn("reopens that administration only if", page)
        self.assertIn("PROLIFIC_PID", page)
        self.assertNotIn("opening the link again starts a new administration", page)
