from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from cdi_forms.models import Choices
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model")
class ChoiceModelTest(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    @tag("model")
    def test_administration_creation(self):
        instance = Choices(choice_set="Test Choice")

        self.assertTrue(isinstance(instance, Choices))
        self.assertEqual(instance.__str__(), f"{instance.choice_set}")

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )
        c = self.client
        c.login(username="super-user", password="password")

        # create test data
        instance = Choices(choice_set="Admin Test Choice")

        # run test
        # response = c.get(get_admin_change_view_url(instance))
        # self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
