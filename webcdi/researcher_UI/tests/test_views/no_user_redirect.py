import logging

from django.test import TestCase
from django.urls import reverse

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class NoUserRedirectTest(TestCase):
    url = reverse("researcher_ui:console")
    login_url = "/accounts/login/?next=/interface/"

    def test_http_status_code_302(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            self.login_url,
        )
