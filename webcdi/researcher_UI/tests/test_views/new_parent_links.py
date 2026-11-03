import datetime
import json
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import (Administration, Demographic, Instrument,
                                  Study, administration_data)
from researcher_UI.utils.random_url_generator import random_url_generator

BACKGROUND_TEMPLATE = "cdi_forms/background_info.html"


def background_payload():
    dob = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime("%m/%d/%Y")
    return {
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


class NewParentTestCase(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.researcher = User.objects.create_user(
            username="link_owner_name", password="x-test-only"
        )
        self.client = Client(raise_request_exception=False)

    def make_study(self, form="WS", name="Link group name", **kwargs):
        return Study.objects.create(
            researcher=self.researcher,
            name=name,
            instrument=Instrument.objects.get(language="English", form=form),
            min_age=12,
            max_age=36,
            demographic=Demographic.objects.get(name="English_Split.json"),
            **kwargs,
        )

    def new_parent_url(self, study, **params):
        url = f"/interface/{self.researcher.username}/{study.name}/new_parent/"
        return f"{url}?{urlencode(params)}" if params else url


class BypassLinkTest(NewParentTestCase):
    """The overflow page offers an uncompensated route once a study is full."""

    def assert_form_opens_and_marks_bypass(self, study, url):
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, BACKGROUND_TEMPLATE)
        response = self.client.post(
            response.redirect_chain[-1][0] if response.redirect_chain else url,
            background_payload(),
        )
        self.assertEqual(response.status_code, 302)
        administration = Administration.objects.get(study=study)
        self.assertTrue(administration.bypass)

    def test_bypass_parameter_on_full_study(self):
        study = self.make_study(subject_cap=0)
        self.assert_form_opens_and_marks_bypass(
            study, self.new_parent_url(study, bypass="true")
        )

    @tag("cat")
    def test_bypass_parameter_on_full_cat_study(self):
        study = self.make_study(form="CAT", subject_cap=0)
        self.assert_form_opens_and_marks_bypass(
            study, self.new_parent_url(study, bypass="true")
        )

    def test_bypass_parameter_on_study_with_room(self):
        study = self.make_study()
        self.assert_form_opens_and_marks_bypass(
            study, self.new_parent_url(study, bypass="true")
        )

    def overflow_response(self, study):
        response = self.client.get(self.new_parent_url(study), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cdi_forms/overflow.html")
        return response

    def test_overflow_link_works(self):
        study = self.make_study(subject_cap=0)
        url = self.overflow_response(study).context["bypass_url"]
        self.assert_form_opens_and_marks_bypass(study, url)

    @tag("cat")
    def test_overflow_link_works_on_cat(self):
        study = self.make_study(form="CAT", subject_cap=0)
        url = self.overflow_response(study).context["bypass_url"]
        self.assert_form_opens_and_marks_bypass(study, url)

    def test_overflow_page_carries_no_researcher_or_group_name(self):
        study = self.make_study(subject_cap=0)
        response = self.overflow_response(study)
        self.assertNotContains(response, self.researcher.username)
        self.assertNotContains(response, study.name.replace(" ", "%20"))
        self.assertNotContains(response, study.name)

    def test_overflow_page_on_no_demographic_study_offers_no_link(self):
        # there is no background form to send a parent to on these studies
        study = self.make_study(no_demographic_boolean=True, subject_cap=0)
        response = self.client.get(
            self.new_parent_url(study, source_id="abc", age=15, sex="m"), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cdi_forms/overflow.html")
        self.assertIsNone(response.context.get("bypass_url"))
        self.assertContains(response, "This study is now completed.")
        self.assertNotContains(response, self.researcher.username)


class SourceIdLinkTest(NewParentTestCase):
    def test_source_id_outside_the_route_format_is_404(self):
        for form, name in (("WS", "Regular"), ("CAT", "CAT")):
            study = self.make_study(form=form, name=name)
            for source_id in ("a b", "a.b", "a@b", "a/b"):
                with self.subTest(form=form, source_id=source_id):
                    response = self.client.get(
                        self.new_parent_url(study, source_id=source_id)
                    )
                    self.assertEqual(response.status_code, 404)
            with self.subTest(form=form, source="child and response"):
                response = self.client.get(
                    self.new_parent_url(study, child="a b", response="c")
                )
                self.assertEqual(response.status_code, 404)

    def test_empty_source_id_is_a_link_without_one(self):
        study = self.make_study()
        response = self.client.get(self.new_parent_url(study, source_id=""))
        self.assertRedirects(
            response,
            f"/form/background/create/{study.pk}/None/",
            fetch_redirect_response=False,
        )

    def test_source_id_in_the_route_format_is_kept(self):
        study = self.make_study()
        for source_id in ("abc", "a-b_c1"):
            with self.subTest(source_id=source_id):
                response = self.client.get(
                    self.new_parent_url(study, source_id=source_id)
                )
                self.assertRedirects(
                    response,
                    f"/form/background/create/{study.pk}/{source_id}/",
                    fetch_redirect_response=False,
                )

    def test_no_demographic_links_may_use_any_source_id(self):
        study = self.make_study(no_demographic_boolean=True)
        response = self.client.get(
            self.new_parent_url(study, source_id="a b", age=15, sex="m")
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            BackgroundInfo.objects.filter(
                administration__study=study, source_id="a b"
            ).exists()
        )


class NoDemographicParametersTest(NewParentTestCase):
    def setUp(self):
        super().setUp()
        self.study = self.make_study(no_demographic_boolean=True)

    def get(self, **params):
        params = {"source_id": "abc", "age": 15, "sex": "m", **params}
        return self.client.get(self.new_parent_url(self.study, **params))

    def test_values_the_fields_cannot_hold_are_404_and_create_nothing(self):
        for params in (
            {"age": "abc"},
            {"age": ""},
            {"age": "15.5"},
            {"age": "-5"},
            {"age": "99999999999"},
            {"sex": "toolong"},
            {"sex": "ß"},  # upper-cases to two characters
            {"offset": "abc"},
            {"offset": ""},
            {"offset": "99999999999"},
            {"offset": "-99999999999"},
            {"source_id": "a" * 256},
            {"event_id": "a" * 256},
        ):
            with self.subTest(params={k: v[:20] for k, v in params.items()}):
                self.assertEqual(self.get(**params).status_code, 404)
                self.assertEqual(
                    Administration.objects.filter(study=self.study).count(), 0
                )

    def test_links_that_work_keep_working(self):
        for number, (params, age, sex) in enumerate(
            (
                ({"sex": "f"}, 15, "F"),
                ({"sex": "M"}, 15, "M"),
                # outside the form's choices but already stored and scored as
                # "not computed": a platform's own coding must keep working
                ({"sex": "1"}, 15, "1"),
                ({"sex": ""}, 15, ""),
                ({"age": 0}, 0, "M"),
                # outside this study's age range: no-demographic links have
                # never been held to it
                ({"age": 40}, 40, "M"),
                ({"age": 999}, 999, "M"),
            )
        ):
            with self.subTest(params=params):
                source_id = f"works{number}"
                response = self.get(source_id=source_id, **params)
                self.assertEqual(response.status_code, 302)
                background = BackgroundInfo.objects.get(source_id=source_id)
                self.assertEqual(background.age, age)
                self.assertEqual(background.sex, sex)
                self.assertTrue(background.administration.completedBackgroundInfo)

    def test_offset_sets_due_date_fields(self):
        for number, (offset, born, diff, early_or_late) in enumerate(
            ((0, 0, 0, None), (-2, 1, 2, "early"), (3, 1, 3, "late"))
        ):
            with self.subTest(offset=offset):
                source_id = f"offset{number}"
                self.assertEqual(
                    self.get(source_id=source_id, offset=offset).status_code, 302
                )
                background = BackgroundInfo.objects.get(source_id=source_id)
                self.assertEqual(background.born_on_due_date, born)
                self.assertEqual(background.due_date_diff, diff)
                self.assertEqual(background.early_or_late, early_or_late)


class SourceIdResumeTest(NewParentTestCase):
    """A no-demographic link opens an existing row only if the link's age and
    sex are those stored on the row."""

    def setUp(self):
        super().setUp()
        self.study = self.make_study(no_demographic_boolean=True)

    def make_row(self, study=None, age=15, sex="M", **kwargs):
        study = study or self.study
        background = {
            "source_id": kwargs.pop("source_id", "abc"),
            "event_id": kwargs.pop("event_id", None),
            "age": age,
            "sex": sex,
        }
        kwargs.setdefault("subject_id", 1)
        kwargs.setdefault("repeat_num", 1)
        kwargs.setdefault("completed", False)
        kwargs.setdefault("completedBackgroundInfo", True)
        kwargs.setdefault("due_date", timezone.now() + datetime.timedelta(days=14))
        row = Administration.objects.create(
            study=study, url_hash=random_url_generator(), **kwargs
        )
        BackgroundInfo.objects.create(administration=row, **background)
        return row

    def get(self, study=None, **params):
        params = {"source_id": "abc", "age": 15, "sex": "m", **params}
        params = {k: v for k, v in params.items() if v is not None}
        return self.client.get(self.new_parent_url(study or self.study, **params))

    def assert_opens(self, response, row):
        self.assertRedirects(
            response,
            reverse("administer_cdi_form", args=[row.url_hash]),
            fetch_redirect_response=False,
        )
        self.assertEqual(Administration.objects.filter(study=row.study).count(), 1)

    def assert_refused(self, response, row):
        """The answer to a value no link may carry; nothing written."""
        self.assertEqual(response.status_code, 404)
        invalid = self.get(study=row.study, source_id="other", age="abc")
        self.assertEqual(invalid.status_code, 404)
        self.assertEqual(response.content, invalid.content)
        self.assertNotIn(row.url_hash.encode(), response.content)
        self.assertEqual(Administration.objects.filter(study=row.study).count(), 1)

    def test_matching_link_opens_the_row(self):
        row = self.make_row()
        self.assert_opens(self.get(), row)

    def test_matching_link_with_an_event_id_opens_the_row(self):
        row = self.make_row(event_id="visit1")
        self.assert_opens(self.get(event_id="visit1"), row)

    def test_any_case_of_the_stored_sex_matches(self):
        for stored, sent in (("M", "m"), ("M", "M"), ("m", "M"), ("1", "1"), ("", "")):
            with self.subTest(stored=stored, sent=sent):
                Administration.objects.filter(study=self.study).delete()
                row = self.make_row(sex=stored)
                self.assert_opens(self.get(sex=sent), row)

    def test_link_with_other_values_does_not_open_or_change_the_row(self):
        row = self.make_row()
        before = BackgroundInfo.objects.filter(administration=row).values().get()
        for params in (
            {"age": 16},
            {"age": 0},
            {"sex": "f"},
            {"sex": ""},
            {"age": 16, "sex": "f"},
        ):
            with self.subTest(params=params):
                self.assert_refused(self.get(**params), row)
                self.assertEqual(
                    BackgroundInfo.objects.filter(administration=row).values().get(),
                    before,
                )

    def test_link_without_age_or_sex_does_not_open_the_row(self):
        row = self.make_row()
        for params in ({"age": None}, {"sex": None}, {"age": None, "sex": None}):
            with self.subTest(params=params):
                self.assert_refused(self.get(**params), row)

    def test_row_with_no_stored_sex_opens_for_no_link(self):
        row = self.make_row(sex=None)
        for sex in ("", "m"):
            with self.subTest(sex=sex):
                self.assert_refused(self.get(sex=sex), row)

    def test_age_is_compared_as_a_whole_number_of_months(self):
        row = self.make_row()
        for age in ("15", "015", " 15", "+15"):
            with self.subTest(age=age):
                self.assert_opens(self.get(age=age), row)
        for age in ("15.0", "15.5", "15m", "15 months", "1y3m", "2021-08-01"):
            with self.subTest(age=age):
                self.assert_refused(self.get(age=age), row)

    def test_stored_values_changed_on_the_background_form_are_the_ones_compared(self):
        row = self.make_row()
        BackgroundInfo.objects.filter(administration=row).update(age=17, sex="F")
        self.assert_refused(self.get(), row)
        self.assert_opens(self.get(age=17, sex="f"), row)

    def test_finished_row_follows_the_same_rule(self):
        row = self.make_row(completed=True)
        self.assert_refused(self.get(age=16), row)
        response = self.get()
        self.assert_opens(response, row)
        response = self.client.get(response["Location"], follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.redirect_chain[-1][0],
            reverse("administration_summary_view", args=[row.url_hash]),
        )

    def test_row_in_progress_follows_the_same_rule(self):
        row = self.make_row(page_number=3)
        self.assert_refused(self.get(sex="f"), row)
        response = self.get()
        self.assert_opens(response, row)
        self.assertRedirects(
            self.client.get(response["Location"]),
            reverse("update_administration_section", args=[row.url_hash, 3]),
            fetch_redirect_response=False,
        )

    def test_expired_row_follows_the_same_rule(self):
        row = self.make_row(due_date=timezone.now() - datetime.timedelta(days=1))
        self.assert_refused(self.get(sex="f"), row)
        self.assert_opens(self.get(), row)

    @tag("cat")
    def test_cat_row_follows_the_same_rule(self):
        study = self.make_study(
            form="CAT", name="CAT resume", no_demographic_boolean=True
        )
        row = self.make_row(study=study)
        self.assert_refused(self.get(study=study, age=16), row)
        response = self.get(study=study)
        self.assert_opens(response, row)
        self.assertRedirects(
            self.client.get(response["Location"]),
            reverse("cat_forms:administer_cat_form", args=[row.url_hash]),
            fetch_redirect_response=False,
        )

    def test_a_new_event_id_is_a_new_row_at_the_childs_new_age(self):
        row = self.make_row(event_id="visit1")
        response = self.get(event_id="visit2", age=18)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(row.url_hash, response["Location"])
        new = BackgroundInfo.objects.get(event_id="visit2")
        self.assertEqual(new.age, 18)
        self.assertEqual(new.administration.subject_id, row.subject_id)
        self.assertEqual(new.administration.repeat_num, 2)
        self.assertEqual(BackgroundInfo.objects.get(event_id="visit1").age, 15)

    def test_two_rows_with_one_source_and_event_open_the_one_that_matches(self):
        self.make_row(age=20)
        row = self.make_row(subject_id=2)
        response = self.get()
        self.assertRedirects(
            response,
            reverse("administer_cdi_form", args=[row.url_hash]),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.get(age=30).status_code, 404)

    def test_source_id_in_another_group_is_not_this_groups_row(self):
        other = self.make_study(name="Other group", no_demographic_boolean=True)
        row = self.make_row(study=other, age=20)
        response = self.get()
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(row.url_hash, response["Location"])

    def test_source_id_link_on_a_study_with_a_background_form_never_opens_a_row(self):
        # these links carry no age or sex: each one starts a new administration
        study = self.make_study(name="With form")
        row = self.make_row(study=study, age=20, sex="F", completed=False)
        BackgroundInfo.objects.filter(administration=row).update(mother_yob=1966)
        for params in ({}, {"age": 20, "sex": "f"}):
            with self.subTest(params=params):
                response = self.client.get(
                    self.new_parent_url(study, source_id="abc", **params), follow=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, BACKGROUND_TEMPLATE)
                self.assertNotContains(response, row.url_hash)
                form = response.context["background_form"]
                self.assertIsNone(form.instance.pk)
                self.assertIsNone(form.instance.mother_yob)

        response = self.client.post(
            f"/form/background/create/{study.pk}/abc/",
            {**background_payload(), "source_id": "abc"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(row.url_hash, response["Location"])
        self.assertEqual(Administration.objects.filter(study=study).count(), 2)
        row.backgroundinfo.refresh_from_db()
        self.assertEqual(row.backgroundinfo.sex, "F")
        self.assertEqual(row.backgroundinfo.mother_yob, 1966)

    def test_api_reads_a_row_by_source_id_for_its_owner_only(self):
        # the researcher's own data: no age or sex is involved, and no row opens
        row = self.make_row()
        url = reverse(
            "api:source_api", kwargs={"pk": self.study.pk, "source_id": "abc"}
        )
        self.researcher.set_password("x-test-only")
        self.researcher.save()
        response = self.client.generic(
            "POST",
            url,
            json.dumps(
                {"username": self.researcher.username, "password": "x-test-only"}
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"Error": "You must select at least 1 completed survey"}
        )
        Administration.objects.filter(pk=row.pk).update(completed=True)
        administration_data.objects.create(
            administration=row, item_ID="item_1", value="produces"
        )
        response = self.client.generic(
            "POST",
            url,
            json.dumps(
                {"username": self.researcher.username, "password": "x-test-only"}
            ),
        )
        self.assertContains(response, row.url_hash)
        response = self.client.generic(
            "POST", url, json.dumps({"username": "nobody", "password": "wrong"})
        )
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(row.url_hash.encode(), response.content)
