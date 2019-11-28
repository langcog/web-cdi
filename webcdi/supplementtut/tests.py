from django.test import TestCase

from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from django.contrib.auth.models import User
from django.urls import reverse
import pickle

from django.conf import settings
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait


# Create your tests here.

class MySeleniumTests(LiveServerTestCase):
    #fixtures = ['user-data.json']

    def setUp(self):
        self.admin = User.objects.create_user(username='JohnLennon', password = 'JohnLennon')
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()

        self.researcher = User.objects.create_user(username='PaulMcCartney', password = 'PaulMcCartney')

    @classmethod
    def setUpClass(cls):
        super(MySeleniumTests, cls).setUpClass()
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chromedriver_path = '/usr/local/bin/chromedriver'
        cls.selenium = webdriver.Chrome(chromedriver_path, chrome_options=chrome_options)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(MySeleniumTests, cls).tearDownClass()

    def admin_login(self):
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.admin.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('JohnLennon')
        self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()
        

    def test_admin_login_to_researchUI(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/interface/'))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.admin.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('JohnLennon')
        self.selenium.find_element_by_id('id_log_in').click()
        url = self.selenium.current_url.split(':')[2][5:]
        self.assertEqual(u'/interface/', url)

    def test_admin_login_admin(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/wcadmin/'))
        self.admin_login()
        welcome_text = self.selenium.find_element_by_id('user-tools').text[:7]
        self.assertEqual(welcome_text, u"WELCOME")

    def test_researcher_login_to_researchUI(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/interface/'))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.researcher.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('PaulMcCartney')
        self.selenium.find_element_by_id('id_log_in').click()
        url = self.selenium.current_url.split(':')[2][5:]
        self.assertEqual(u'/interface/', url)

    def test_researcher_login_to_admin_fails(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/wcadmin/'))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.researcher.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('PaulMcCartney')
        self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()

        url = self.selenium.current_url.split(':')[2][5:]
        self.assertEqual(u'/wcadmin/login/?next=/wcadmin/', url)

    def test_registration(self):
        #complete registration
        self.selenium.get('%s%s' % (self.live_server_url,'/registration/register/'))
        self.selenium.find_element_by_id('id_username').send_keys("test_researcher")
        self.selenium.find_element_by_id("id_email1").send_keys('hjsmehta@gmail.com')
        self.selenium.find_element_by_id("id_email2").send_keys('hjsmehta@gmail.com')
        self.selenium.find_element_by_id("id_first_name").send_keys('Test')
        self.selenium.find_element_by_id("id_last_name").send_keys('Researcher')
        self.selenium.find_element_by_id("id_institution").send_keys('Fake University')
        self.selenium.find_element_by_id("id_position").send_keys('RA')
        self.selenium.find_element_by_id("id_register").click()
        url = self.selenium.current_url.split(':')[2][5:]
        self.assertEqual(u'/registration/register/complete/', url)

        # now make them valid
        self.selenium.get('%s%s' % (self.live_server_url,'/wcadmin/registration/registrationprofile/'))
        self.admin_login()
        self.selenium.find_element_by_link_text('test_researcher').click()
        self.selenium.find_element_by_name('_save').click()

        #set them to active
        self.selenium.get('%s%s' % (self.live_server_url,'/wcadmin/auth/user/'))
        self.selenium.find_element_by_link_text('test_researcher').click()
        self.selenium.find_element_by_link_text('this form').click()
        self.selenium.find_element_by_id("id_password1").send_keys('pw')
        self.selenium.find_element_by_id("id_password2").send_keys('pw')
        self.selenium.find_element_by_xpath('//input[@value="Change password"]').click()
        self.selenium.find_element_by_id("id_is_active").click()
        self.selenium.find_element_by_name('_save').click()
        self.selenium.find_element_by_xpath("//a[@href='/wcadmin/logout/']").click()

        #login as new test researcher
        self.selenium.get('%s%s' % (self.live_server_url, '/interface/'))
        self.selenium.find_element_by_id('id_username').send_keys("test_researcher")
        self.selenium.find_element_by_id("id_password").send_keys('pw')
        self.selenium.find_element_by_id('id_log_in').click()
        url = self.selenium.current_url.split(':')[2][5:]
        self.selenium.find_element_by_id("study-form")