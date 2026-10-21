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

    def test_login_only_pages_redirect_anonymous_users(self):
        # #630: these must send anonymous users to login, not raise (500)
        for name in [
            "researcher_ui:get_demographic_forms",
            "researcher_ui:get_charge_status",
            "researcher_ui:profile",
            "researcher_ui:change_password",
        ]:
            url = reverse(name)
            response = self.client.get(url)
            self.assertRedirects(
                response,
                f"/accounts/login/?next={url}",
                fetch_redirect_response=False,
                msg_prefix=name,
            )

