from django.test import TestCase, tag
from django.contrib.auth.models import User
from researcher_UI.models import Demographic
from researcher_UI.tests.utils import get_admin_change_view_url, get_admin_changelist_view_url
from django.contrib.auth.models import User
# models test


@tag("model")
class DemographicModelTest(TestCase):
    def setUp(self) -> None:

        self.demographic = Demographic.objects.create(
            name="Demographic Model Test", path="path/to/demographic/files/"
        )

    def test_demographic_creation(self):
        instance = self.demographic

        self.assertTrue(isinstance(instance, Demographic))
        self.assertEqual(instance.__str__(), f"{instance.name}")

    @tag('admin')
    def test_admin(self):
        self.user = User.objects.create_superuser(
            'super-user', "content_tester@goldenstandard.com", 'password'
        )
        c = self.client
        c.login(username='super-user', password='password')

        # create test data
        instance = self.demographic

        # run test
        response = c.get(get_admin_change_view_url(instance))
        self.assertEqual(response.status_code, 200)

        response = c.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)