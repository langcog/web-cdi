from django.contrib.auth.models import User
from django.test import Client, TestCase, tag
from django.urls import reverse

from brookes.models import BrookesCode


def get_admin_change_view_url(obj: object) -> str:
    return reverse(
        "admin:{}_{}_change".format(obj._meta.app_label, type(obj).__name__.lower()),
        args=(obj.pk,),
    )


def get_admin_changelist_view_url(obj: object) -> str:
    return reverse(
        "admin:{}_{}_changelist".format(
            obj._meta.app_label, type(obj).__name__.lower()
        ),
    )


@tag("admin")
class BrookesCodeAdminTest(TestCase):
    def setUp(self):
        # Create some object to perform the action on
        self.brookes_code = BrookesCode.objects.create()

        # Create auth user for views using api request factory
        self.username = "content_tester"
        self.password = "goldenstandard"
        self.user = User.objects.create_superuser(
            self.username, "test@example.com", self.password
        )

    def test_change_view_loads_normally(self):
        # prepare client

        c = Client()
        c.login(username=self.username, password=self.password)

        # create test data
        brookes_code = BrookesCode.objects.create()

        # run test
        response = c.get(get_admin_change_view_url(brookes_code))
        self.assertEqual(response.status_code, 200)

    def test_create_50_codes_actions(self):
        data = {
            "action": "create_50_codes",
            "_selected_action": [
                self.brookes_code.code,
            ],
        }
        change_url = get_admin_changelist_view_url(self.brookes_code)
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(change_url, data)
        self.client.logout()

        self.assertEqual(BrookesCode.objects.all().count(), 51)
        self.assertEqual(response.status_code, 302)
