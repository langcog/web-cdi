from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from cdi_forms.models import Zipcode
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model", "zip")
class ZipcodeModelTest(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    @tag("model")
    def test_administration_creation(self):
        instance = Zipcode(zip_code="12345")

        self.assertTrue(isinstance(instance, Zipcode))
        self.assertEqual(instance.__str__(), f"{instance.zip_code}")

    """
    No Admin for Zipcode model
    @tag('admin')
    def test_admin(self):
        self.user = User.objects.create_superuser(
            'super-user', "content_tester@goldenstandard.com", 'password'
        )
        c = self.client
        c.login(username='super-user', password='password')

        # create test data
        instance = Zipcode(zip_code='23456')

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 302)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 302)
    """
