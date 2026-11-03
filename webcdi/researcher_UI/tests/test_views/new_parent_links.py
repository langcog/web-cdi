import datetime
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.test import Client, TestCase, tag

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import Administration, Demographic, Instrument, Study

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
