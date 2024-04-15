from typing import Any

from django.contrib.auth.models import User
from django.test import TestCase, tag

from researcher_UI.models import Researcher
from researcher_UI.tests.utils import get_admin_change_view_url, get_admin_changelist_view_url
# models test


@tag("model")
class ResearcherModelTest(TestCase):

    def setUp(self, **kwargs: Any) -> Any:

        user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        self.researcher, created = Researcher.objects.get_or_create(
            user=user,
        )

        self.researcher.institution = "Test Institution"
        self.researcher.position = "Test Position"
        self.researcher.save()

    def test_researcher_creation(self):
        instance = self.researcher

        self.assertTrue(isinstance(instance, Researcher))
        self.assertEqual(
            instance.__str__(),
            f"{instance.user.first_name} {instance.user.last_name} ({instance.position}, {instance.institution})",
        )

    @tag('admin')
    def test_admin(self):
        self.user = User.objects.create_superuser(
            'super-user', "content_tester@goldenstandard.com", 'password'
        )
        c = self.client
        c.login(username='super-user', password='password')

        # create test data
        instance = self.researcher

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)

