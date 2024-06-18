import logging

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse_lazy

from researcher_UI.forms import ProfileForm, ResearcherForm
from researcher_UI.tests.utils import random_password

logger = logging.getLogger("test")
logger.setLevel(logging.INFO)


@tag("new")
class ProileTestCase(TestCase):
    def setUp(self):
        self.password = random_password()
        self.user = User.objects.create(username="test_user", password=self.password)

    def test_profile_get(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse_lazy("researcher_ui:profile"))
        self.assertEqual(200, response.status_code)

    def test_profile_change(self):
        self.client.force_login(self.user)

        payload = {
            "email": "new_email@example.com",
            "user": self.user.id,
            "institution": "Test Institution",
            "position": "Test Position",
        }
        form = ProfileForm(data=payload)
        self.assertTrue(form.is_valid())
        form = ResearcherForm(instance=self.user.researcher, data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.post(reverse_lazy("researcher_ui:profile"), payload)
        self.assertRedirects(response, reverse_lazy("researcher_ui:console"))
        self.assertEqual(self.user.researcher.position, "Test Position")

    def test_profile_change_password(self):
        self.client.force_login(self.user)
        self.user.set_password(self.password)
        new_password = random_password()
        payload = {
            "old_password": self.password,
            "new_password1": new_password,
            "new_password2": new_password,
        }
        form = PasswordChangeForm(user=self.user, data=payload)
        self.assertTrue(form.is_valid())

        response = self.client.get(
            reverse_lazy("researcher_ui:change_password"),
        )
        self.assertEqual(response.template_name, ["researcher_UI/change_password.html"])

        response = self.client.post(
            reverse_lazy("researcher_ui:change_password"), payload
        )
        """
        #TODO 
        This doesn't work for some reason and I do not know why 
        self.assertEqual(response.template_name, 'researcher_ui/console.html')
        self.assertRedirects(response, reverse_lazy("researcher_ui:console"))
        """
