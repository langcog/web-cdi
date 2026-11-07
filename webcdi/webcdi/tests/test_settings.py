import logging
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase, override_settings, tag
from django.utils.log import AdminEmailHandler, configure_logging

from webcdi.settings import JSON_LOGGING, _parse_env_admins, _parse_env_list
from webcdi.utils import is_true


@tag("settings")
class JsonLoggingTest(SimpleTestCase):
    """Containers log JSON to stdout and never email request errors."""

    def tearDown(self):
        configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)

    @override_settings(DEBUG=False, ADMINS=[("Admin", "admin@example.com")])
    def test_request_errors_are_logged_not_emailed(self):
        configure_logging(settings.LOGGING_CONFIG, JSON_LOGGING)
        # capture at the root, so the record passes every logger on the way
        with mock.patch.object(AdminEmailHandler, "emit") as emit, self.assertLogs(
            level="ERROR"
        ):
            logging.getLogger("django.request").error("Internal Server Error: /x/")
        emit.assert_not_called()


@tag("settings")
class EnvParsingTest(SimpleTestCase):
    """The settings env-var parsers and DEBUG coercion are load-bearing for
    deploy; the refactor that introduced them was verified by a manual dump
    diff, so lock the behavior in here."""

    def test_parse_env_list_unquoted_shorthand(self):
        self.assertEqual(
            _parse_env_list("[localhost,127.0.0.1,web]"),
            ["localhost", "127.0.0.1", "web"],
        )

    def test_parse_env_list_quoted_literal(self):
        self.assertEqual(_parse_env_list('["localhost", "web"]'), ["localhost", "web"])

    def test_parse_env_admins_unquoted_shorthand(self):
        # shorthand strips whitespace, including inside names
        self.assertEqual(
            _parse_env_admins("[(Local Admin,a@b.com)]"),
            [("LocalAdmin", "a@b.com")],
        )

    def test_parse_env_admins_quoted_literal(self):
        self.assertEqual(
            _parse_env_admins('[("Local Admin", "a@b.com")]'),
            [("Local Admin", "a@b.com")],
        )

    def test_is_true_truthy_strings(self):
        self.assertTrue(is_true("true"))
        self.assertTrue(is_true("True"))
        self.assertTrue(is_true(True))
        self.assertTrue(is_true(1))

    def test_is_true_falsey_strings(self):
        # the bug this fixed: bool("False") is True, so DEBUG=False used to
        # enable debug; is_true("False") must be False
        self.assertFalse(is_true("False"))
        self.assertFalse(is_true("false"))
        self.assertFalse(is_true(""))
        self.assertFalse(is_true(False))
        self.assertFalse(is_true(0))
