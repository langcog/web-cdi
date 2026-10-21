import datetime
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, tag
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Study)
from researcher_UI.utils.completion_notice import MAX_ATTEMPTS

POST = "researcher_UI.utils.completion_notice.requests.post"


def respond(status_code):
    return mock.Mock(return_value=mock.Mock(status_code=status_code))


@tag("model")
class CompletionNoticeTest(TestCase):
    """#723: the notice goes out once, on the transition to completed; failed
    notices are retried by crontab_scoring, at most MAX_ATTEMPTS in all."""

    def setUp(self):
        user = User.objects.create_user(username="notice_user", password="secret")
        family = InstrumentFamily.objects.create(
            name="Completion Notice Family", chargeable=False
        )
        instrument = Instrument.objects.create(
            name="Completion Notice Instrument",
            language="Test Language",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=family,
        )
        self.study = Study.objects.create(
            researcher=user,
            name="Completion Notice Study",
            instrument=instrument,
            send_completion_flag_url="https://example.com/notify",
            completion_data={
                "record_id": "{{source_id}}",
                "redcap_event_name": "{{event_id}}",
                "webcdi_completion_status": "1",
            },
        )
        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash="completion-notice-test-hash",
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=14),
        )
        BackgroundInfo.objects.create(
            administration=self.administration,
            age=12,
            source_id="src-1",
            event_id="event-1",
        )

    def complete(self, status_code=200):
        post = respond(status_code)
        with mock.patch(POST, post), self.captureOnCommitCallbacks(execute=True):
            self.administration.completed = True
            self.administration.save()
        self.administration.refresh_from_db()
        return post

    def run_scheduled_job(self, status_code=200, at=None):
        post = respond(status_code)
        with mock.patch(POST, post):
            if at is None:
                call_command("crontab_scoring")
            else:
                with mock.patch(
                    "researcher_UI.utils.completion_notice.timezone.now",
                    return_value=at,
                ):
                    call_command("crontab_scoring")
        self.administration.refresh_from_db()
        return post

    def test_one_notice_on_completion(self):
        post = self.complete()
        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args, ("https://example.com/notify",))
        self.assertEqual(
            kwargs["data"],
            {
                "record_id": "src-1",
                "redcap_event_name": "event-1",
                "webcdi_completion_status": "1",
            },
        )
        self.assertEqual(self.administration.send_completion_flag_url_response, 200)
        self.assertEqual(self.administration.completion_notice_attempts, 1)
        self.assertIsNone(self.administration.completion_notice_next_attempt)
        # the study's template is not overwritten by the substitution
        self.study.refresh_from_db()
        self.assertEqual(self.study.completion_data["record_id"], "{{source_id}}")

    def test_one_notice_when_completion_triggers_scoring(self):
        # outside tests, post_save_completed_handler scores the administration
        # (a nested save) on the same transition
        with mock.patch("researcher_UI.signals.TESTING", False):
            post = self.complete()
        post.assert_called_once()
        self.assertTrue(self.administration.scored)
        self.assertEqual(self.administration.completion_notice_attempts, 1)

    def test_no_notice_on_later_saves(self):
        self.complete(status_code=500)
        post = respond(200)
        with mock.patch(POST, post), self.captureOnCommitCallbacks(execute=True):
            self.administration.scored = False
            self.administration.save()
            Administration.objects.get(pk=self.administration.pk).save()
        post.assert_not_called()

    def test_no_notice_on_bulk_rescoring(self):
        self.complete(status_code=500)
        post = respond(200)
        with mock.patch(POST, post), self.captureOnCommitCallbacks(execute=True):
            call_command("update_summary_data", study_id=self.study.pk)
        post.assert_not_called()

    def test_no_notice_for_previously_completed_administrations(self):
        # administrations completed before this change: response stored, nothing pending
        Administration.objects.filter(pk=self.administration.pk).update(
            completed=True, send_completion_flag_url_response=500
        )
        self.administration.refresh_from_db()
        post = respond(200)
        with mock.patch(POST, post), self.captureOnCommitCallbacks(execute=True):
            self.administration.save()
            call_command("update_summary_data", study_id=self.study.pk)
        post.assert_not_called()
        post = self.run_scheduled_job(
            at=timezone.now() + datetime.timedelta(days=1)
        )
        post.assert_not_called()

    def test_no_notice_without_url(self):
        self.study.send_completion_flag_url = None
        self.study.save()
        self.administration.study.refresh_from_db()
        post = self.complete()
        post.assert_not_called()
        self.assertEqual(self.administration.completion_notice_attempts, 0)

    def test_retry_from_scheduled_job_stops_after_success(self):
        self.complete(status_code=500)
        self.assertEqual(self.administration.completion_notice_attempts, 1)
        next_attempt = self.administration.completion_notice_next_attempt
        self.assertIsNotNone(next_attempt)

        # not due yet
        post = self.run_scheduled_job()
        post.assert_not_called()

        post = self.run_scheduled_job(status_code=200, at=next_attempt)
        post.assert_called_once()
        self.assertEqual(self.administration.send_completion_flag_url_response, 200)
        self.assertEqual(self.administration.completion_notice_attempts, 2)
        self.assertIsNone(self.administration.completion_notice_next_attempt)

        post = self.run_scheduled_job(at=next_attempt + datetime.timedelta(days=1))
        post.assert_not_called()

    def test_retries_stop_after_max_attempts(self):
        self.complete(status_code=500)
        later = timezone.now()
        for attempt in range(2, MAX_ATTEMPTS + 1):
            later += datetime.timedelta(hours=1)
            post = self.run_scheduled_job(status_code=503, at=later)
            post.assert_called_once()
            self.assertEqual(self.administration.completion_notice_attempts, attempt)
        self.assertEqual(self.administration.send_completion_flag_url_response, 503)
        self.assertIsNone(self.administration.completion_notice_next_attempt)

        post = self.run_scheduled_job(at=later + datetime.timedelta(days=1))
        post.assert_not_called()
        self.assertEqual(self.administration.completion_notice_attempts, MAX_ATTEMPTS)

    def test_connection_error_is_retried(self):
        import requests

        post = mock.Mock(side_effect=requests.ConnectionError("refused"))
        with mock.patch(POST, post), self.captureOnCommitCallbacks(execute=True):
            self.administration.completed = True
            self.administration.save()
        self.administration.refresh_from_db()
        post.assert_called_once()
        self.assertIsNone(self.administration.send_completion_flag_url_response)
        self.assertEqual(self.administration.completion_notice_attempts, 1)
        self.assertIsNotNone(self.administration.completion_notice_next_attempt)
