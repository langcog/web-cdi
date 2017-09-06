from django.test import TestCase, LiveServerTestCase, Client
from selenium.webdriver.firefox.webdriver import WebDriver
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import pickle, os

from django.conf import settings
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from subprocess import Popen, PIPE
from django.core.management import call_command



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
        """ Shortcut for WebDriverWait"""
        try:
            return WebDriverWait(self, timeout).until(lambda driver : driver.find_css(css_selector))
        except:
            self.quit()

class SeleniumTestCase(LiveServerTestCase):  
    def open(self, url):
        self.wd.get("%s%s" % (self.live_server_url, url))

class Auth(SeleniumTestCase):

    def setUp(self):
        
        process = Popen(['psql', settings.DATABASES['default']['TEST']['NAME'], '-U', settings.DATABASES['default']['USER']], stdout=PIPE, stdin=PIPE)
        filename = 'webcdi-backup.sql'
        output = process.communicate('\i ' + filename)[0]

        self.admin = User.objects.create_user(username='admin', password = 'pw')
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()

        self.client = Client()
        login = self.client.login(username='admin', password = 'pw')
        self.assertTrue(login)
        self.wd = CustomWebDriver()
        self.wd.implicitly_wait(10)

        cookie = self.client.cookies['sessionid']
        self.open('/')  # initial page load
        self.wd.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.wd.refresh() # refresh page for logged in user

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

    def test_admin_login(self):
        self.open('/interface/')
        self.wd.wait_for_css("input[value='Logout']",5).click()
        self.wd.find_css('#id_username').send_keys("admin")
        self.wd.find_css("#id_password").send_keys('pw')
        self.wd.find_css("#id_login").click()
        self.wd.wait_for_css("#study-form",5)

    def test_registration(self):
        self.open('/registration/register/')
        self.wd.find_css('#id_username').send_keys("test_researcher")
        self.wd.find_css("#id_email1").send_keys('dkellier@stanford.edu')
        self.wd.find_css("#id_email2").send_keys('dkellier@stanford.edu')
        self.wd.find_css("#id_name").send_keys('Test Researcher')
        self.wd.find_css("#id_institution").send_keys('Fake University')
        self.wd.find_css("#id_position").send_keys('RA')
        self.wd.find_css("#id_register").click()
        self.wd.wait_for_css("#success",5)

        self.open('/admin/registration/registrationprofile/')
        self.wd.find_element_by_link_text('test_researcher').click()
        self.wd.find_element_by_name('_save').click()

        self.open('/admin/auth/user/')
        self.wd.find_element_by_link_text('test_researcher').click()
        self.wd.find_element_by_link_text('this form').click()
        self.wd.find_css("#id_password1").send_keys('pw')
        self.wd.find_css("#id_password2").send_keys('pw')
        self.wd.wait_for_css("input[value='Change password']",5).click()
        self.wd.find_css("#id_is_active").click()
        self.wd.find_element_by_name('_save').click()
        self.wd.wait_for_css("a[href='/admin/logout/']",5).click()

        self.open('/interface/')
        self.wd.find_css('#id_username').send_keys("test_researcher")
        self.wd.find_css("#id_password").send_keys('pw')
        self.wd.find_css("#id_login").click()
        self.wd.wait_for_css("#study-form",5)

