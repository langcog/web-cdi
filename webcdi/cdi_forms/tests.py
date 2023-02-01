from django.test import TestCase, LiveServerTestCase, Client
from selenium.webdriver.chrome.webdriver import WebDriver
from django.urls import reverse
import pickle, os, time, random

from django.conf import settings
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

from django.test.utils import override_settings
from subprocess import Popen, PIPE
from django.core.management import call_command

from django.contrib.auth.models import User
from researcher_UI.models import *
from researcher_UI.tests import generate_fake_results
from .models import *

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


class CustomWebDriver(WebDriver):
    """Our own WebDriver with some helpers added"""

    def find_css(self, css_selector):
        """Shortcut to find elements by CSS. Returns either a list or singleton"""
        elems = self.find_elements_by_css_selector(css_selector)
        found = len(elems)
        if found == 1:
            return elems[0]
        elif not elems:
            raise NoSuchElementException(css_selector)
        return elems

    def wait_for_css(self, css_selector, timeout=7):
        """Shortcut for WebDriverWait"""
        try:
            return WebDriverWait(self, timeout).until(
                lambda driver: driver.find_css(css_selector)
            )
        except:
            self.quit()


class SeleniumTestCase(LiveServerTestCase):
    """
    A base test case for selenium, providing hepler methods for generating
    clients and logging in profiles.
    """

    def open(self, url):
        self.wd.get("%s%s" % (self.live_server_url, url))


@override_settings(DEBUG=True)
class TestParentInterface(SeleniumTestCase):
    fixtures = [
        "researcher_UI/fixtures/instrument-fixtures.json",
        "cdi_forms/fixtures/choices.json",
    ]

    def setUp(self):
        # setUp is where you setup call fixture creation scripts
        # and instantiate the WebDriver, which in turns loads up the browser.

        self.admin = User.objects.create_user(username="admin", password="pw")
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()

        self.researcher = User.objects.create_user(username="researcher", password="pw")

        self.instrument = instrument.objects.get(name="English_WS")

        self.study_obj = study.objects.create(
            researcher=self.admin,
            name="Test Study",
            instrument=self.instrument,
            min_age=16,
            max_age=30,
        )
        self.study_obj.save()

        self.client = Client()
        login = self.client.login(username="admin", password="pw")
        self.assertTrue(login)

        self.wd = CustomWebDriver()
        self.wd.implicitly_wait(10)
        cookie = self.client.cookies["sessionid"]
        self.open("/")  # initial page load
        self.wd.add_cookie(
            {"name": "sessionid", "value": cookie.value, "secure": False, "path": "/"}
        )
        self.wd.refresh()  # refresh page for logged in user

    def tearDown(self):
        # Don't forget to call quit on your webdriver, so that
        # the browser is closed after the tests are ran
        self.wd.quit()

    def find_css(self, css_selector):
        """Shortcut to find elements by CSS. Returns either a list or singleton"""
        elems = self.find_elements_by_css_selector(css_selector)
        found = len(elems)
        if found == 1:
            return elems[0]
        elif not elems:
            raise NoSuchElementException(css_selector)
        return elems

    def researcher_login(self):
        self.open("/interface/")
        username_input = self.wd.find_css("username")
        username_input.send_keys(self.researcher.username)
        password_input = self.wd.find_element_by_name("password")
        password_input.send_keys("pw")
        self.wd.find_element_by_id("id_log_in").click()

    def test_parent_UI(self):
        call_command("populate_items")
        test_url = reverse(
            "researcher_ui:administer_new_parent",
            args=[self.study_obj.researcher, self.study_obj.name],
        )
        self.open(test_url)

        try:
            self.wd.wait_for_css("#okaybtn", 5).click()
        except:  # NoSuchElementException:
            pass

        self.wd.execute_script("fastforward()")
        self.wd.wait_for_css('input[name="btn-next"]', 5)[1].click()

        time.sleep(5)
        self.wd.execute_script("fastforward()")

        # not sure why I have to do it like this, but deosn't get the alert if any quicker
        WebDriverWait(self.wd, 10).until(
            EC.element_to_be_clickable((By.ID, "id_submit_btn2"))
        )
        time.sleep(5)
        WebDriverWait(self.wd, 10).until(
            EC.element_to_be_clickable((By.ID, "id_submit_btn2"))
        ).click()

        alert = self.wd.switch_to_alert()
        alert.accept()
        try:
            WebDriverWait(self.wd, 10).until(
                EC.presence_of_element_located((By.ID, "id_results"))
            )
            self.assertEqual(True, True)
        except:
            self.assertEqual(True, "Did not go to results page")

    def test_parent_UI_with_waiver(self):
        self.study_obj.waiver = "<p>This is a Waiver Example</p>"
        self.study_obj.save()

        test_url = reverse(
            "researcher_ui:administer_new_parent",
            args=[self.study_obj.researcher, self.study_obj.name],
        )
        self.open(test_url)

        try:
            self.wd.wait_for_css("#okaybtn", 5).click()
        except:  # NoSuchElementException:
            pass

        time.sleep(5)
        try:
            WebDriverWait(self.wd, 10).until(
                EC.presence_of_element_located((By.ID, "consent_waiver"))
            )
            self.assertEqual(True, True)
        except:
            self.assertEqual(True, "Waiver Modal didn't open")

    def test_parent_UI_dutch_background_info(self):
        call_command("populate_items")
        self.instrument = instrument.objects.get(name="Dutch_WG")
        self.study_obj = study.objects.create(
            researcher=self.admin,
            name="Dutch Test Study",
            instrument=self.instrument,
            min_age=16,
            max_age=30,
        )
        self.study_obj.save()

        test_url = reverse(
            "researcher_ui:administer_new_parent",
            args=[self.study_obj.researcher, self.study_obj.name],
        )
        self.open(test_url)

        # complete background page
        self.wd.execute_script("fastforward()")
        self.wd.wait_for_css('input[name="btn-next"]', 5)[1].click()
        time.sleep(5)
        # complete questionnaire
        self.wd.execute_script("fastforward()")
        WebDriverWait(self.wd, 10).until(
            EC.element_to_be_clickable((By.ID, "id_submit_btn2"))
        )
        time.sleep(5)
        WebDriverWait(self.wd, 10).until(
            EC.element_to_be_clickable((By.ID, "id_submit_btn2"))
        ).click()
        alert = self.wd.switch_to_alert()
        alert.accept()
        # complete backpage
        self.wd.execute_script("dutch_backpage_fastforward()")
        WebDriverWait(self.wd, 10).until(
            EC.element_to_be_clickable((By.ID, "id_submit_btn"))
        ).click()

        try:
            WebDriverWait(self.wd, 10).until(
                EC.presence_of_element_located((By.ID, "id_results"))
            )
            self.assertEqual(True, True)
        except:
            self.assertEqual(True, "Did not go to results page")
