from django.test import SimpleTestCase, tag

from webcdi.settings import _parse_env_admins, _parse_env_list
from webcdi.utils import is_true


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
