import logging

from django.contrib.auth.models import User
from django.test import Client, TestCase

from researcher_UI.tests.utils import random_password

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class LoginTestCase(TestCase):
    def setUp(self):
        self.password = random_password()
        User.objects.create(username="henry", password=self.password)

    def test_user_can_login(self):
        c = Client()
        response = c.post(
            "/accounts/login/", {"username": "henry", "password": self.password}
        )
        self.assertEqual(200, response.status_code)
