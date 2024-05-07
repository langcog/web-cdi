import datetime
import os
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, LiveServerTestCase
from django.test.utils import override_settings
from django.urls import reverse
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoSuchElementException,
                                        UnexpectedTagNameException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from cdi_forms.models import *
from researcher_UI.models import Demographic, Instrument, Study

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

import logging

from django.test import LiveServerTestCase, tag
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)

# Create your tests here.


def scroll_and_click(passed_in_driver, object):
    x = object.location["x"]
    y = object.location["y"]
    scroll_by_coord = f"window.scrollTo({x},{y});"
    scroll_nav_out_of_way = "window.scrollBy(0, -120);"
    passed_in_driver.execute_script(scroll_by_coord)
    passed_in_driver.execute_script(scroll_nav_out_of_way)
    actions = ActionChains(passed_in_driver)
    actions.move_to_element(object).perform()
    actions.click()
    actions.perform()


@tag("selenium", "login")
class WebSiteOpensTests(LiveServerTestCase):
    LiveServerTestCase.host = "web"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        cls.selenium = webdriver.Remote(
            command_executor="http://selenium:4444", options=options
        )
        cls.selenium.implicitly_wait(10)

    def test_visit_home_age(self):
        self.selenium.get(f"{self.live_server_url}")
        self.assertIn(self.selenium.title, "Web CDI")

    def test_visit_login_page(self):
        self.selenium.get(f"{self.live_server_url}/accounts/login/")
        self.assertIn(self.selenium.title, "Login")


@tag("selenium")
class TestParentInterface(LiveServerTestCase):
    LiveServerTestCase.host = "web"
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        # setUp is where you setup call fixture creation scripts
        # and instantiate the WebDriver, which in turns loads up the browser.

        self.admin = User.objects.create_user(username="admin", password="pw")
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()

        self.researcher = User.objects.create_user(username="researcher", password="pw")

        self.instrument = Instrument.objects.get(name="English_WS")

        self.study_obj = Study.objects.create(
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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.selenium = webdriver.Remote("http://selenium:4444", options=options)
        cls.selenium.implicitly_wait(1)

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
        self.selenium.get(f"{self.live_server_url}/accounts/login/")
        username_input = self.selenium.find_element("name", "username")
        username_input.send_keys(self.researcher.username)
        password_input = self.selenium.find_element("name", "password")
        password_input.send_keys("pw")
        self.selenium.find_element("name", "login").click()

    def complete_background_info(self):
        try:
            element = Select(self.selenium.find_element(By.ID, "id_form_filler"))
            element.select_by_value("mother")
        except NoSuchElementException:
            pass

        try:
            element = self.selenium.find_element(By.ID, "id_child_dob")
            now = datetime.datetime.now() - datetime.timedelta(days=500)
            input_date = now.strftime("%m/%d/%Y")
            element.send_keys(input_date)
        except NoSuchElementException:
            pass
        except ElementNotInteractableException:
            pass

        try:
            element = self.selenium.find_element(By.ID, "id_sex_1")
            scroll_and_click(self.selenium, element)

        except NoSuchElementException:
            pass

        try:
            element = Select(self.selenium.find_element(By.ID, "id_birth_order"))
            element.select_by_value("1")
        except NoSuchElementException:
            pass
        except UnexpectedTagNameException:
            pass

        try:
            element = self.selenium.find_element(By.ID, "id_multi_birth_boolean_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass

        try:
            element = Select(self.selenium.find_element(By.ID, "id_birth_weight_lb"))
            element.select_by_value("1.0")
        except NoSuchElementException:
            pass
        except UnexpectedTagNameException:
            pass

        try:
            element = Select(self.selenium.find_element(By.ID, "id_birth_weight_kg"))
            element.select_by_value("2.5")
        except NoSuchElementException:
            pass
        except UnexpectedTagNameException:
            pass

        try:
            element = self.selenium.find_element(By.ID, "id_born_on_due_date_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass

        try:
            element = Select(self.selenium.find_element(By.ID, "id_primary_caregiver"))
            element.select_by_value("mother")
        except NoSuchElementException:
            pass
        except UnexpectedTagNameException:
            pass

        try:
            element = Select(self.selenium.find_element(By.ID, "id_mother_yob"))
            element.select_by_value("1977")
        except NoSuchElementException:
            pass
        except UnexpectedTagNameException:
            pass

        try:
            element = Select(self.selenium.find_element(By.ID, "id_mother_education"))
            element.select_by_value("18")
        except NoSuchElementException:
            pass
        except UnexpectedTagNameException:
            pass

        try:
            element = Select(self.selenium.find_element(By.ID, "id_annual_income"))
            element.select_by_value("Prefer not to disclose")
        except NoSuchElementException:
            pass
        except UnexpectedTagNameException:
            pass

        try:
            element = Select(self.selenium.find_element(By.ID, "id_caregiver_info"))
            element.select_by_value("2")
        except NoSuchElementException:
            pass
        except UnexpectedTagNameException:
            pass

        try:
            element = self.selenium.find_element(By.ID, "id_other_languages_boolean_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass

        try:
            element = self.selenium.find_element(By.ID, "id_ear_infections_boolean_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass
        try:
            element = self.selenium.find_element(By.ID, "id_hearing_loss_boolean_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass
        try:
            element = self.selenium.find_element(By.ID, "id_vision_problems_boolean_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass
        try:
            element = self.selenium.find_element(By.ID, "id_illnesses_boolean_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass
        try:
            element = self.selenium.find_element(By.ID, "id_services_boolean_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass
        try:
            element = self.selenium.find_element(By.ID, "id_worried_boolean_1")
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass
        try:
            element = self.selenium.find_element(
                By.ID, "id_learning_disability_boolean_1"
            )
            scroll_and_click(self.selenium, element)
        except NoSuchElementException:
            pass

        self.selenium.find_element(By.NAME, "btn-next").click()
        if self.selenium.find_elements(By.ID, "id_submit_btn"):
            self.selenium.find_element(By.ID, "id_submit_btn").click()

    def complete_administration(self):
        completed = False
        while not completed:
            if self.selenium.find_elements(By.ID, "id_child_dob"):
                self.selenium.find_element(By.ID, "id_child_dob")
                self.complete_background_info()
            if self.selenium.find_elements(By.ID, "page_number"):
                element = self.selenium.find_element(By.ID, "page_number")
                if element.get_attribute("value") == "0":
                    # instruction page
                    element = self.selenium.find_element(By.ID, "id_next_page")
                    scroll_and_click(self.selenium, element)
            if self.selenium.find_elements(By.ID, "id_next"):
                element = self.selenium.find_element(By.ID, "id_next")
                els = self.selenium.find_elements(By.XPATH, "//input[@type='checkbox']")
                for el in els:
                    scroll_and_click(self.selenium, el)
                els = self.selenium.find_elements(By.XPATH, "//input[@type='radio']")
                for el in els:
                    scroll_and_click(self.selenium, el)
                element = self.selenium.find_element(By.NAME, "btn-next")
                scroll_and_click(self.selenium, element)
            if self.selenium.find_elements(By.ID, "id_submit_btn2"):
                completed = True
                element = self.selenium.find_element(By.ID, "id_submit_btn2")
                scroll_and_click(self.selenium, element)
        self.selenium.switch_to.alert.accept()

    def test_parent_UI(self):
        test_url = reverse(
            "researcher_ui:administer_new_parent",
            args=[self.study_obj.researcher, self.study_obj.name],
        )

        self.selenium.get(f"{self.live_server_url}/{test_url}")

        try:
            self.selenium.wait_for_css("#okaybtn", 5).click()
        except:  # NoSuchElementException:
            pass

        self.complete_administration()

        # not sure why I have to do it like this, but deosn't get the alert if any quicker

        try:
            WebDriverWait(self.selenium, 10).until(
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
        self.selenium.get(f"{self.live_server_url}/{test_url}")

        try:
            self.selenium.wait_for_css("#okaybtn", 5).click()
        except:  # NoSuchElementException:
            pass

        time.sleep(5)
        try:
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, "consent_waiver"))
            )
            self.assertEqual(True, True)
        except:
            self.assertEqual(True, "Waiver Modal didn't open")

    def test_parent_UI_dutch_background_info(self):
        self.instrument = Instrument.objects.get(name="Dutch_WG")
        demographic = Demographic.objects.get(name="Dutch_Split.json")
        self.study_obj = Study.objects.create(
            researcher=self.admin,
            name="Dutch Test Study",
            instrument=self.instrument,
            min_age=16,
            max_age=30,
            demographic=demographic,
            birth_weight_units="kg",
        )
        self.study_obj.save()

        test_url = reverse(
            "researcher_ui:administer_new_parent",
            args=[self.study_obj.researcher, self.study_obj.name],
        )
        self.selenium.get(f"{self.live_server_url}/{test_url}")

        self.complete_administration()

        # this will pick up the back page
        self.complete_background_info()

        try:
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, "id_results"))
            )
            self.assertEqual(True, True)
        except:
            self.assertEqual(True, "Did not go to results page")
