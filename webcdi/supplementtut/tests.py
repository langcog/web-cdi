from django.test import TestCase

from django.test import LiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import pickle

from django.conf import settings
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait



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
    """
    A base test case for selenium, providing hepler methods for generating
    clients and logging in profiles.
    """
        
    def open(self, url):
        self.wd.get("%s%s" % (self.live_server_url, url))

class Auth(SeleniumTestCase):

    def setUp(self):
        # setUp is where you setup call fixture creation scripts
        # and instantiate the WebDriver, which in turns loads up the browser.
        User.objects.create_superuser(username='admin',
                                      password='pw',
                                      email='dkellier@stanford.edu')

        # Instantiating the WebDriver will load your browser
        self.wd = CustomWebDriver()
        self.wd.implicitly_wait(10)



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

    # Just like Django tests, any method that is a Selenium test should
    # start with the "test_" prefix.
    def test_admin_login(self):
        """
        Django Admin login test
        """
        # Open the admin index page
        self.open('/interface/')

        # Selenium knows it has to wait for page loads (except for AJAX requests)
        # so we don't need to do anything about that, and can just
        # call find_css. Since we can chain methods, we can
        # call the built-in send_keys method right away to change the
        # value of the field
        self.wd.find_css('#id_username').send_keys("admin")
        # for the password, we can now just call find_css since we know the page
        # has been rendered
        self.wd.find_css("#id_password").send_keys('pw')
        # You're not limited to CSS selectors only, check
        # http://seleniumhq.org/docs/03_webdriver.html for 
        # a more compreehensive documentation.
        self.wd.find_css("#id_login").click()
        # Again, after submiting the form, we'll use the find_css helper
        # method and pass as a CSS selector, an id that will only exist
        # on the index page and not the login page
        self.wd.wait_for_css("#study-form",5)

    def test_registration(self):

        self.open('/registration/register/')


        self.wd.find_css('#id_username').send_keys("test_researcher")
        # for the password, we can now just call find_css since we know the page
        # has been rendered
        self.wd.find_css("#id_email1").send_keys('dkellier@stanford.edu')
        self.wd.find_css("#id_email2").send_keys('dkellier@stanford.edu')

        self.wd.find_css("#id_name").send_keys('Test Researcher')
        self.wd.find_css("#id_institution").send_keys('Fake University')
        self.wd.find_css("#id_position").send_keys('RA')
        # You're not limited to CSS selectors only, check
        # http://seleniumhq.org/docs/03_webdriver.html for 
        # a more compreehensive documentation.
        self.wd.find_css("#id_register").click()
        # Again, after submiting the form, we'll use the find_css helper
        # method and pass as a CSS selector, an id that will only exist
        # on the index page and not the login page
        self.wd.wait_for_css("#success",5)

        pickle.dump( self.wd.get_cookies() , open("cookies.pkl","wb"))



    	self.wd.get("%s%s" % (self.live_server_url, '/admin/registration/registrationprofile/'))
    	self.wd.find_css('#id_username').send_keys("admin")
    	self.wd.find_css("#id_password").send_keys('pw')
    	self.wd.wait_for_css("input[value='Log in']",5).click()


    	cookies = pickle.load(open("cookies.pkl", "rb"))
    	for cookie in cookies:
    		self.wd.add_cookie(cookie)

    	self.wd.find_element_by_link_text('test_researcher').click()

    	self.wd.find_element_by_name('_save').click()

    	pickle.dump( self.wd.get_cookies() , open("cookies.pkl","wb"))




    	self.wd.get("%s%s" % (self.live_server_url, '/admin/auth/user/'))
    	cookies = pickle.load(open("cookies.pkl", "rb"))
    	for cookie in cookies:
    		self.wd.add_cookie(cookie)

    	self.wd.find_element_by_link_text('test_researcher').click()
    	self.wd.find_element_by_link_text('this form').click()

        self.wd.find_css("#id_password1").send_keys('pw')
        self.wd.find_css("#id_password2").send_keys('pw')

        self.wd.find_css("#id_is_active").click()
        self.wd.find_element_by_name('_save').click()
    	

    	self.wd.wait_for_css("input[value='Change password']",5).click()

    	pickle.dump( self.wd.get_cookies() , open("cookies.pkl","wb"))



    	self.wd.get("%s%s" % (self.live_server_url, '/interface/'))
    	cookies = pickle.load(open("cookies.pkl", "rb"))
    	for cookie in cookies:
    		self.wd.add_cookie(cookie)

    	self.wd.wait_for_css("input[value='Logout']",5).click()
    	
        self.wd.find_css('#id_username').send_keys("test_researcher")
        # for the password, we can now just call find_css since we know the page
        # has been rendered
        self.wd.find_css("#id_password").send_keys('pw')
        # You're not limited to CSS selectors only, check
        # http://seleniumhq.org/docs/03_webdriver.html for 
        # a more compreehensive documentation.
        self.wd.find_css("#id_login").click()
        # Again, after submiting the form, we'll use the find_css helper
        # method and pass as a CSS selector, an id that will only exist
        # on the index page and not the login page
        self.wd.wait_for_css("#study-form",5)

