from typing import Any

from django.contrib.auth.models import User
from django.test import TestCase, tag


from researcher_UI.tests.utils import get_admin_change_view_url, get_admin_changelist_view_url
# models test


@tag("model")
class UserModelTest(TestCase):

    def setUp(self, **kwargs: Any) -> Any:

        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

    @tag('admin')
    def test_admin(self):
        self.user = User.objects.create_superuser(
            'super-user', "content_tester@goldenstandard.com", 'password'
        )
        c = self.client
        c.login(username='super-user', password='password')

        # create test data
        instance = self.user

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)

    @tag('admin')
    def test_action_email_list(self):
        data = {
            "action": "email_list",
            "_selected_action": [
                self.user.id,
            ],
        }
        change_url = get_admin_changelist_view_url(self.user)
        User.objects.create_superuser(
            'super-user', "content_tester@goldenstandard.com", 'password'
        )
        self.client.login(username='super-user', password='password')
        response = self.client.post(change_url, data)
        self.client.logout()

        self.assertEqual(response.status_code, 200)