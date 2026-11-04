import datetime
import json
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, RequestFactory, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.cat_forms.models import CatResponse
from cdi_forms.models import BackgroundInfo, Instrument_Forms, requests_log
from cdi_forms.views.utils import prefilled_cdi_data
from researcher_UI.admin.admin_actions import scoring_data, scoring_summary
from researcher_UI.models import (Administration, Demographic, Instrument,
                                  Study, SummaryData, administration_data)
from researcher_UI.tests import generate_fake_results
from researcher_UI.utils.random_url_generator import random_url_generator
from researcher_UI.views.download_data_views import PDFAdministrationDetailView


class DeletedRowTestCase(TestCase):
    """Researchers delete an administration by making it inactive."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.researcher = User.objects.create_user(
            username="deleted_rows_owner", password="x-test-only"
        )
        self.client = Client(raise_request_exception=False)

    def make_study(self, form="WS", name="Deleted rows", **kwargs):
        return Study.objects.create(
            researcher=self.researcher,
            name=name,
            instrument=Instrument.objects.get(language="English", form=form),
            min_age=12,
            max_age=36,
            demographic=Demographic.objects.get(name="English_Split.json"),
            **kwargs,
        )

    def make_administration(self, study, subject_id=1, repeat_num=1, **kwargs):
        kwargs.setdefault("completed", False)
        kwargs.setdefault("due_date", timezone.now() + datetime.timedelta(days=14))
        return Administration.objects.create(
            study=study,
            subject_id=subject_id,
            repeat_num=repeat_num,
            url_hash=random_url_generator(),
            **kwargs,
        )


class DeletedRowDownloadTest(DeletedRowTestCase):
    def setUp(self):
        super().setUp()
        self.study = self.make_study()
        generate_fake_results(self.study, 2)
        self.kept = Administration.objects.get(study=self.study, subject_id=1)
        self.deleted = Administration.objects.get(study=self.study, subject_id=2)
        Administration.objects.filter(pk=self.deleted.pk).update(is_active=False)
        self.client.force_login(self.researcher)

    def download(self, action, select=False):
        payload = {action: action}
        if select:
            payload["select_col"] = [self.kept.pk, self.deleted.pk]
        return self.client.post(
            reverse("researcher_ui:console_study", args=[self.study.pk]), payload
        )

    def assert_only_kept_row(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn(self.kept.url_hash, content)
        self.assertNotIn(self.deleted.url_hash, content)

    def test_whole_group_downloads_leave_out_a_deleted_row(self):
        for action in (
            "download-study-csv",
            "download-study-csv-adjusted",
            "download-summary-csv",
        ):
            with self.subTest(action=action):
                self.assert_only_kept_row(self.download(action))

    def test_selected_downloads_leave_out_a_deleted_row(self):
        for action in (
            "download-selected",
            "download-selected-adjusted",
            "download-selected-summary",
            "download-links",
        ):
            with self.subTest(action=action):
                self.assert_only_kept_row(self.download(action, select=True))

    def test_admin_downloads_leave_out_a_deleted_row(self):
        request = RequestFactory().post("/")
        request.user = self.researcher
        for action in (scoring_data, scoring_summary):
            with self.subTest(action=action.__name__):
                self.assert_only_kept_row(
                    action(None, request, Study.objects.filter(pk=self.study.pk))
                )

    def test_clinical_report_leaves_out_a_deleted_row(self):
        view = PDFAdministrationDetailView()
        view.object = self.study
        for url in ("/", f"/?id={self.kept.pk}&id={self.deleted.pk}"):
            with self.subTest(url=url):
                view.request = RequestFactory().get(url)
                self.assertEqual(list(view.completed_administrations()), [self.kept])

    def post_api(self, url):
        self.researcher.set_password("x-test-only")
        self.researcher.save()
        payload = {"username": self.researcher.username, "password": "x-test-only"}
        return self.client.generic("POST", url, json.dumps(payload))

    def test_api_leaves_out_a_deleted_row(self):
        BackgroundInfo.objects.filter(administration=self.kept).update(source_id="kept")
        BackgroundInfo.objects.filter(administration=self.deleted).update(
            source_id="gone", event_id="e1"
        )
        pk = self.study.pk
        for name, kwargs in (
            ("api:study_api", {"pk": pk}),
            ("api:source_api", {"pk": pk, "source_id": "kept"}),
            ("api:administration_api", {"pk": pk, "administration_id": self.kept.pk}),
        ):
            with self.subTest(view=name):
                response = self.post_api(reverse(name, kwargs=kwargs))
                self.assertEqual(response.status_code, 200)
                content = response.content.decode()
                self.assertIn(self.kept.url_hash, content)
                self.assertNotIn(self.deleted.url_hash, content)

        for name, kwargs in (
            ("api:source_api", {"pk": pk, "source_id": "gone"}),
            ("api:event_api", {"pk": pk, "source_id": "gone", "event_id": "e1"}),
            (
                "api:administration_api",
                {"pk": pk, "administration_id": self.deleted.pk},
            ),
        ):
            with self.subTest(view=name, row="deleted"):
                response = self.post_api(reverse(name, kwargs=kwargs))
                self.assertEqual(
                    response.json(),
                    {"Error": "You must select at least 1 completed survey"},
                )

    def test_study_api_with_only_deleted_rows_has_nothing_to_return(self):
        Administration.objects.filter(study=self.study).update(is_active=False)
        response = self.post_api(reverse("api:study_api", kwargs={"pk": self.study.pk}))
        self.assertEqual(
            response.json(), {"Error": "You must select at least 1 completed survey"}
        )


@tag("cat")
class DeletedRowCatDownloadTest(DeletedRowTestCase):
    def setUp(self):
        super().setUp()
        self.study = self.make_study(form="CAT")
        self.kept = self.make_administration(self.study, 1, completed=True)
        self.deleted = self.make_administration(
            self.study, 2, completed=True, is_active=False
        )
        for administration in (self.kept, self.deleted):
            BackgroundInfo.objects.create(administration=administration, age=24)
            CatResponse.objects.create(
                administration=administration,
                est_theta=0.5,
                administered_words=["ball"],
                administered_responses=[True],
                administered_items=[1],
            )
        self.client.force_login(self.researcher)

    def test_cat_downloads_leave_out_a_deleted_row(self):
        for action, select in (
            ("download-study-csv", False),
            ("download-study-csv-adjusted", False),
            ("download-summary-csv", False),
            ("download-selected", True),
            ("download-selected-adjusted", True),
            ("download-selected-summary", True),
        ):
            with self.subTest(action=action):
                payload = {action: action}
                if select:
                    payload["select_col"] = [self.kept.pk, self.deleted.pk]
                response = self.client.post(
                    reverse("researcher_ui:console_study", args=[self.study.pk]),
                    payload,
                )
                self.assertEqual(response.status_code, 200)
                content = response.content.decode()
                self.assertIn(self.kept.url_hash, content)
                self.assertNotIn(self.deleted.url_hash, content)


class DeletedRowPrefillTest(DeletedRowTestCase):
    def word_item(self, study):
        return Instrument_Forms.objects.filter(
            instrument=study.instrument, item_type="word"
        ).first().itemID

    def test_answers_are_not_copied_from_a_deleted_row(self):
        study = self.make_study(prefilled_data=2)
        item_id = self.word_item(study)
        old = self.make_administration(study, completed=True, is_active=False)
        administration_data.objects.create(
            administration=old, item_ID=item_id, value="produces"
        )
        new = self.make_administration(study, repeat_num=2, completedBackgroundInfo=True)
        BackgroundInfo.objects.create(administration=new, age=24)

        prefilled_cdi_data(new)
        self.assertFalse(administration_data.objects.filter(administration=new).exists())

        response = self.client.get(
            reverse("update_administration_section", args=[new.url_hash, 1])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(administration_data.objects.filter(administration=new).exists())

    def test_answers_come_from_the_latest_row_still_active(self):
        study = self.make_study(prefilled_data=2)
        item_id = self.word_item(study)
        for repeat_num, value, is_active in (
            (1, "understands", True),
            (2, "produces", False),
        ):
            old = self.make_administration(
                study, repeat_num=repeat_num, completed=True, is_active=is_active
            )
            administration_data.objects.create(
                administration=old, item_ID=item_id, value=value
            )
        new = self.make_administration(study, repeat_num=3, completedBackgroundInfo=True)
        BackgroundInfo.objects.create(administration=new, age=24)

        prefilled_cdi_data(new)
        self.assertEqual(
            administration_data.objects.get(administration=new, item_ID=item_id).value,
            "understands",
        )

    def background_form_instance(self, is_active):
        study = self.make_study(name=f"Background {is_active}", prefilled_data=1)
        old = self.make_administration(
            study, completedBackgroundInfo=True, is_active=is_active
        )
        old_background = BackgroundInfo.objects.create(
            administration=old, age=24, mother_yob=1966
        )
        new = self.make_administration(study, repeat_num=2)
        BackgroundInfo.objects.create(administration=new)
        response = self.client.get(reverse("background-info", args=[new.url_hash]))
        self.assertEqual(response.status_code, 200)
        return response.context["background_form"].instance, old_background

    def test_background_is_not_prefilled_from_a_deleted_row(self):
        instance, old_background = self.background_form_instance(is_active=False)
        self.assertNotEqual(instance.pk, old_background.pk)
        self.assertIsNone(instance.mother_yob)

    def test_background_is_prefilled_from_an_active_row(self):
        instance, old_background = self.background_form_instance(is_active=True)
        self.assertEqual(instance.pk, old_background.pk)


class DeletedRowCapTest(DeletedRowTestCase):
    def test_participant_cap_does_not_count_a_deleted_row(self):
        study = self.make_study(subject_cap=1)
        deleted = self.make_administration(study, completed=True)
        url = reverse(
            "researcher_ui:administer_new_parent",
            kwargs={"username": self.researcher.username, "study_name": study.name},
        )
        overflow = reverse("researcher_ui:overflow", args=[study.pk])
        self.assertRedirects(self.client.get(url), overflow, fetch_redirect_response=False)

        Administration.objects.filter(pk=deleted.pk).update(is_active=False)
        self.assertRedirects(
            self.client.get(url),
            f"/form/background/create/{study.pk}/None/",
            fetch_redirect_response=False,
        )

    def test_slots_left_does_not_count_a_deleted_row(self):
        study = self.make_study(subject_cap=3, study_group="paired")
        self.make_administration(study, 1, completed=True)
        self.make_administration(study, 2, completed=True, is_active=False)
        self.make_administration(study, 3, completed=False)
        response = self.client.get(
            reverse(
                "find_paired_studies",
                args=[self.researcher.username, study.name, "abc"],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["possible_studies"][0].slots_left, 2)


class DeletedRowRepeatNumTest(DeletedRowTestCase):
    """A deleted row keeps its number, so no two rows of a child share one."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.researcher)

    def new_repeat_num(self, study):
        return (
            Administration.objects.filter(study=study, subject_id=1)
            .order_by("-repeat_num")
            .first()
            .repeat_num
        )

    def test_administer_selected_counts_a_deleted_row(self):
        study = self.make_study()
        self.make_administration(study, repeat_num=1, is_active=False)
        kept = self.make_administration(study, repeat_num=2)
        with mock.patch.object(Study, "valid_code", return_value=True):
            self.client.post(
                reverse("researcher_ui:console_study", args=[study.pk]),
                {"administer-selected": "1", "select_col": [kept.pk]},
            )
        self.assertEqual(self.new_repeat_num(study), 3)

    def test_administer_new_counts_a_deleted_row(self):
        study = self.make_study()
        self.make_administration(study, repeat_num=1, is_active=False)
        response = self.client.post(
            reverse("researcher_ui:administer_new", kwargs={"pk": study.pk}),
            {"new_subject_ids": "1", "autogenerate_count": ""},
        )
        self.assertEqual(response.json()["stat"], "ok")
        self.assertEqual(self.new_repeat_num(study), 2)

    def test_new_event_on_a_link_counts_a_deleted_row(self):
        study = self.make_study(no_demographic_boolean=True)
        deleted = self.make_administration(study, repeat_num=1, is_active=False)
        BackgroundInfo.objects.create(
            administration=deleted, source_id="abc", event_id="one", age=15, sex="M"
        )
        response = self.client.get(
            reverse(
                "researcher_ui:administer_new_parent",
                kwargs={"username": self.researcher.username, "study_name": study.name},
            ),
            {"source_id": "abc", "event_id": "two", "age": 16, "sex": "M"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.new_repeat_num(study), 2)


class DeletedRowParticipantLinkTest(DeletedRowTestCase):
    """A link to a deleted row is a 404 and leaves the database as it was."""

    REGULAR_ROUTES = (
        ("background-info", ()),
        ("backpage-background-info", ()),
        ("administer_cdi_form", ()),
        ("instructions", ()),
        ("update_administration", ()),
        ("update_administration_section", (1,)),
        ("update_administration_section_previous", (2, "previous")),
        ("administration_summary_view", ()),
        ("contact", ()),
        ("administration-view", ()),
        ("administration-pdf-view", ()),
    )
    CAT_ROUTES = (
        ("cat_forms:background-info", ()),
        ("cat_forms:backpage-background-info", ()),
        ("cat_forms:administer_cat_form", ()),
    )

    def make_row(self, study, **kwargs):
        row = self.make_administration(
            study, completedBackgroundInfo=True, page_number=2, **kwargs
        )
        BackgroundInfo.objects.create(administration=row, age=24, sex="F")
        return row

    def snapshot(self, row):
        return (
            Administration.objects.filter(pk=row.pk).values().get(),
            BackgroundInfo.objects.filter(administration=row).values().get(),
            list(
                administration_data.objects.filter(administration=row)
                .order_by("item_ID")
                .values("item_ID", "value")
            ),
            list(CatResponse.objects.filter(administration=row).values()),
            requests_log.objects.count(),
            Administration.objects.count(),
            len(mail.outbox),
        )

    def assert_routes(self, row, routes, assertion):
        for name, args in routes:
            url = reverse(name, args=[row.url_hash, *args])
            with self.subTest(view=name):
                assertion(self.client.get(url).status_code)

    def post_everything(self, row, routes, item_id):
        before = self.snapshot(row)
        payload = {
            "btn-next": "Next",
            "btn-save": "Save",
            "btn-submit": "Submit",
            "cdi-form": "1",
            "next": "3",
            "email": "parent@example.com",
            "message": "hello",
            item_id: "produces",
        }
        for name, args in routes:
            url = reverse(name, args=[row.url_hash, *args])
            with self.subTest(view=name, method="POST"):
                # the pdf route takes no POST at all
                self.assertIn(self.client.post(url, payload).status_code, (404, 405))
                self.assertEqual(self.snapshot(row), before)

    def test_every_route_of_a_deleted_row_in_progress_is_404(self):
        study = self.make_study()
        row = self.make_row(study)
        item_id = (
            Instrument_Forms.objects.filter(
                instrument=study.instrument, item_type="word"
            )
            .first()
            .itemID
        )
        administration_data.objects.create(
            administration=row, item_ID=item_id, value="understands"
        )
        Administration.objects.filter(pk=row.pk).update(is_active=False)
        before = self.snapshot(row)

        self.assert_routes(
            row, self.REGULAR_ROUTES, lambda code: self.assertEqual(code, 404)
        )
        self.post_everything(row, self.REGULAR_ROUTES, item_id)

        for name, data in (
            ("save_answer", {item_id: "produces"}),
            (
                "update-administration-data-item",
                {"check": "true", "item": item_id, "value": "produces"},
            ),
        ):
            with self.subTest(view=name):
                response = self.client.post(
                    reverse(name), {"hash_id": row.url_hash, **data}
                )
                self.assertEqual(response.status_code, 404)
        self.assertEqual(self.snapshot(row), before)

        # the researcher can bring the row back and the parent carries on
        Administration.objects.filter(pk=row.pk).update(is_active=True)
        self.assert_routes(
            row, self.REGULAR_ROUTES, lambda code: self.assertNotEqual(code, 404)
        )
        self.assertEqual(
            administration_data.objects.get(administration=row).value, "understands"
        )

    def test_a_finished_deleted_row_is_404(self):
        study = self.make_study()
        row = self.make_row(study, completed=True, is_active=False)
        self.assert_routes(
            row, self.REGULAR_ROUTES, lambda code: self.assertEqual(code, 404)
        )

    @tag("cat")
    def test_every_route_of_a_deleted_cat_row_is_404(self):
        study = self.make_study(form="CAT")
        row = self.make_row(study)
        CatResponse.objects.create(
            administration=row,
            est_theta=0.5,
            administered_words=["ball"],
            administered_responses=[True],
            administered_items=[1],
        )
        Administration.objects.filter(pk=row.pk).update(is_active=False)
        before = self.snapshot(row)

        self.assert_routes(
            row, self.CAT_ROUTES, lambda code: self.assertEqual(code, 404)
        )
        response = self.client.post(
            reverse("cat_forms:cat_answer", args=[row.url_hash]),
            json.dumps(
                {"index": 2, "definition": "cat", "response": True, "est_theta": 1.0}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            self.client.post(
                reverse("cat_forms:administer_cat_form", args=[row.url_hash]),
                {"btn-back": "1"},
            ).status_code,
            404,
        )
        self.assertEqual(self.snapshot(row), before)

        Administration.objects.filter(pk=row.pk).update(is_active=True)
        self.assert_routes(
            row, self.CAT_ROUTES, lambda code: self.assertNotEqual(code, 404)
        )

    def test_every_route_of_a_row_in_a_deleted_group_is_404(self):
        study = self.make_study()
        row = self.make_row(study)
        item_id = (
            Instrument_Forms.objects.filter(
                instrument=study.instrument, item_type="word"
            )
            .first()
            .itemID
        )
        administration_data.objects.create(
            administration=row, item_ID=item_id, value="understands"
        )
        Study.objects.filter(pk=study.pk).update(active=False)
        before = self.snapshot(row)

        self.assert_routes(
            row, self.REGULAR_ROUTES, lambda code: self.assertEqual(code, 404)
        )
        self.post_everything(row, self.REGULAR_ROUTES, item_id)
        for name, data in (
            ("save_answer", {item_id: "produces"}),
            (
                "update-administration-data-item",
                {"check": "true", "item": item_id, "value": "produces"},
            ),
        ):
            with self.subTest(view=name):
                response = self.client.post(
                    reverse(name), {"hash_id": row.url_hash, **data}
                )
                self.assertEqual(response.status_code, 404)
        self.assertEqual(self.snapshot(row), before)

        # staff can bring the group back and the parent carries on
        Study.objects.filter(pk=study.pk).update(active=True)
        self.assert_routes(
            row, self.REGULAR_ROUTES, lambda code: self.assertNotEqual(code, 404)
        )

    @tag("cat")
    def test_every_route_of_a_cat_row_in_a_deleted_group_is_404(self):
        study = self.make_study(form="CAT")
        row = self.make_row(study)
        Study.objects.filter(pk=study.pk).update(active=False)
        before = self.snapshot(row)

        self.assert_routes(
            row, self.CAT_ROUTES, lambda code: self.assertEqual(code, 404)
        )
        response = self.client.post(
            reverse("cat_forms:cat_answer", args=[row.url_hash]),
            json.dumps(
                {"index": 2, "definition": "cat", "response": True, "est_theta": 1.0}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.snapshot(row), before)

    def test_reusable_link_of_a_deleted_group_is_closed(self):
        for form, name in (
            ("WS", "create-new-background-info"),
            ("CAT", "cat_forms:create-new-background-info"),
        ):
            study = self.make_study(form=form, name=f"Deleted {form}", active=False)
            with self.subTest(form=form):
                for url in (
                    reverse(
                        "researcher_ui:administer_new_parent",
                        kwargs={
                            "username": self.researcher.username,
                            "study_name": study.name,
                        },
                    ),
                    reverse(
                        name,
                        kwargs={
                            "study_id": study.pk,
                            "bypass": True,
                            "source_id": "None",
                        },
                    ),
                ):
                    response = self.client.get(url)
                    self.assertTemplateUsed(
                        response, "cdi_forms/single_reusable_link_inactive.html"
                    )
                self.assertFalse(Administration.objects.filter(study=study).exists())

    def test_source_link_of_a_deleted_group_does_not_open_a_row(self):
        study = self.make_study(no_demographic_boolean=True, active=False)
        row = self.make_administration(study, completedBackgroundInfo=True)
        BackgroundInfo.objects.create(
            administration=row, source_id="abc", age=15, sex="M"
        )
        response = self.client.get(
            reverse(
                "researcher_ui:administer_new_parent",
                kwargs={"username": self.researcher.username, "study_name": study.name},
            ),
            {"source_id": "abc", "age": 15, "sex": "m"},
        )
        self.assertTemplateUsed(
            response, "cdi_forms/single_reusable_link_inactive.html"
        )
        self.assertEqual(Administration.objects.filter(study=study).count(), 1)

    def test_source_id_link_to_a_deleted_row_does_not_open_it_or_make_a_new_one(self):
        study = self.make_study(no_demographic_boolean=True)
        row = self.make_administration(study, completedBackgroundInfo=True, is_active=False)
        BackgroundInfo.objects.create(
            administration=row, source_id="abc", age=15, sex="M"
        )
        response = self.client.get(
            reverse(
                "researcher_ui:administer_new_parent",
                kwargs={"username": self.researcher.username, "study_name": study.name},
            ),
            {"source_id": "abc", "age": 15, "sex": "m"},
            follow=True,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Administration.objects.filter(study=study).count(), 1)


class DeletingKeepsDataTest(DeletedRowTestCase):
    """Delete hides data from the researcher; nothing leaves the database."""

    def setUp(self):
        super().setUp()
        self.study = self.make_study()
        self.row = self.make_administration(self.study, completed=True)
        administration_data.objects.create(
            administration=self.row, item_ID="item_1", value="produces"
        )
        SummaryData.objects.create(administration=self.row, title="Score", value="1")
        self.client.force_login(self.researcher)
        self.url = reverse("researcher_ui:console_study", args=[self.study.pk])

    def assert_data_kept(self):
        self.assertTrue(Study.objects.filter(pk=self.study.pk).exists())
        self.assertTrue(Administration.objects.filter(pk=self.row.pk).exists())
        self.assertEqual(
            administration_data.objects.get(administration=self.row).value, "produces"
        )
        self.assertEqual(SummaryData.objects.get(administration=self.row).value, "1")

    def test_deleting_an_administration_keeps_it_in_the_database(self):
        self.client.post(
            self.url, {"delete-selected": "", "select_col": [str(self.row.pk)]}
        )
        self.row.refresh_from_db()
        self.assertFalse(self.row.is_active)
        self.assert_data_kept()

    def test_deleting_a_group_keeps_it_in_the_database(self):
        self.client.post(self.url, {"delete-study": "delete-study"})
        self.study.refresh_from_db()
        self.assertFalse(self.study.active)
        self.assert_data_kept()

    def test_group_page_tells_the_researcher_how_to_get_data_back(self):
        for url in (
            self.url,
            reverse("researcher_ui:rename_study", args=[self.study.pk]),
        ):
            with self.subTest(url=url):
                page = self.client.get(url).content.decode()
                self.assertIn("webcdi-contact@stanford.edu", page)
                self.assertNotIn("permanently", page)


class AdminCannotRemoveDataTest(DeletedRowTestCase):
    """The Django admin holds to the same rule as the researcher's Delete."""

    def setUp(self):
        super().setUp()
        self.staff = User.objects.create_superuser(
            username="delete_staff", password="x-test-only"
        )
        self.study = self.make_study()
        self.row = self.make_administration(self.study, is_active=False)
        self.client.force_login(self.staff)

    def assert_nothing_removed(self):
        self.assertTrue(User.objects.filter(pk=self.researcher.pk).exists())
        self.assertTrue(Study.objects.filter(pk=self.study.pk).exists())
        self.assertTrue(Administration.objects.filter(pk=self.row.pk).exists())

    def test_no_delete_page_or_bulk_delete_for_groups_and_administrations(self):
        for model, pk in (
            ("study", self.study.pk),
            ("administration", self.row.pk),
        ):
            with self.subTest(model=model):
                url = reverse(f"admin:researcher_UI_{model}_delete", args=[pk])
                self.assertEqual(
                    self.client.post(url, {"post": "yes"}).status_code, 403
                )
                self.client.post(
                    reverse(f"admin:researcher_UI_{model}_changelist"),
                    {
                        "action": "delete_selected",
                        "_selected_action": [pk],
                        "post": "yes",
                    },
                )
                self.assert_nothing_removed()

    def test_deleting_a_user_cannot_take_their_groups_along(self):
        self.client.post(
            reverse("admin:auth_user_delete", args=[self.researcher.pk]), {"post": "yes"}
        )
        self.assert_nothing_removed()

    def test_deleting_an_instrument_cannot_take_its_groups_along(self):
        self.client.post(
            reverse(
                "admin:researcher_UI_instrument_delete",
                args=[self.study.instrument.pk],
            ),
            {"post": "yes"},
        )
        self.assert_nothing_removed()
        self.assertTrue(Instrument.objects.filter(pk=self.study.instrument.pk).exists())

    def test_staff_can_still_restore_an_administration(self):
        self.client.post(
            reverse("admin:researcher_UI_administration_changelist"),
            {"action": "set_is_active_true", "_selected_action": [self.row.pk]},
        )
        self.row.refresh_from_db()
        self.assertTrue(self.row.is_active)
