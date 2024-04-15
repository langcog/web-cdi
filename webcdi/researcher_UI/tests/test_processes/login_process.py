import logging

from django.test import LiveServerTestCase, tag
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger("selenium")
logger.setLevel(logging.ERROR)

# Create your tests here.


@tag("selenium", "login")
class WebSiteOpensTests(LiveServerTestCase):
    LiveServerTestCase.host = "web"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        cls.firefox = webdriver.Remote(
            command_executor="http://selenium:4444", options=options
        )
        cls.firefox.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.firefox.quit()
        super().tearDownClass()

    def test_visit_home_age(self):
        self.firefox.get(f"{self.live_server_url}")
        self.assertIn(self.firefox.title, "Web CDI")

    def test_visit_login_page(self):
        self.firefox.get(f"{self.live_server_url}/accounts/login/")
        self.assertIn(self.firefox.title, "Login")
