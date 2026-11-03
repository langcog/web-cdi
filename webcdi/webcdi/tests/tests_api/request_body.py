from django.contrib.auth.models import User
from django.test import TestCase

from researcher_UI.models import Instrument, Study


class APIRequestBodyTest(TestCase):
    """The API answers a body without usable credentials with a client error."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        user = User.objects.create_user("api_body_test", password="x-test-only")
        study = Study.objects.create(
            researcher=user,
            name="API body",
            instrument=Instrument.objects.get(language="English", form="WS"),
        )
        self.paths = [
            f"/api/study/{study.pk}/",
            f"/api/study/{study.pk}/source/abc/",
            f"/api/study/{study.pk}/source/abc/def/",
            f"/api/study/{study.pk}/administration/1/",
        ]

    def test_unusable_bodies_are_client_errors(self):
        for label, body in [
            ("empty", ""),
            ("not JSON", "not json"),
            ("not UTF-8", b"\xff\xfe"),
            ("JSON list", "[1, 2]"),
            ("JSON number", "1"),
            ("no password", '{"username": "api_body_test"}'),
            ("no username", '{"password": "x"}'),
        ]:
            for path in self.paths:
                with self.subTest(body=label, path=path):
                    response = self.client.post(
                        path, body, content_type="application/json"
                    )
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("error", response.json())

    def test_wrong_credentials_are_still_401(self):
        for path in self.paths:
            with self.subTest(path=path):
                response = self.client.post(
                    path,
                    '{"username": "api_body_test", "password": "wrong"}',
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 401)
