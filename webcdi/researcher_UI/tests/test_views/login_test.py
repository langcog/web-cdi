import logging

from django.contrib.auth.models import User
from django.test import Client, TestCase

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class LoginTestCase(TestCase):
    def setUp(self):
        User.objects.create(username="henry", password="poiuytre12")

    def test_user_can_login(self):
        c = Client()
        response = c.post(
            "/accounts/login/", {"username": "henry", "password": "poiuytre12"}
        )
        self.assertEqual(200, response.status_code)
