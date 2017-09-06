from django.test import TestCase, LiveServerTestCase, Client
from selenium.webdriver.firefox.webdriver import WebDriver
from django.core.urlresolvers import reverse
import pickle, os

from django.conf import settings
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from subprocess import Popen, PIPE
from django.core.management import call_command

from django.contrib.auth.models import User
from researcher_UI.models import *
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

class TestParentInterface(SeleniumTestCase):

    def setUp(self):
        # setUp is where you setup call fixture creation scripts
        # and instantiate the WebDriver, which in turns loads up the browser.
        
        process = Popen(['psql', settings.DATABASES['default']['TEST']['NAME'], '-U', settings.DATABASES['default']['USER']], stdout=PIPE, stdin=PIPE)
        filename = 'webcdi-backup.sql'
        output = process.communicate('\i ' + filename)[0]

        self.admin = User.objects.create_user(username='admin', password = 'pw')
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()
        self.study_obj = study.objects.get(name = 'Debug-V6-WG', researcher = User.objects.get(username='langcoglab'))
        self.study_obj.pk = None
        self.study_obj.name = 'Test'
        self.study_obj.researcher = self.admin
        self.study_obj.save()

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

    def generate_fake_results(study_obj,autogenerate_count):

        new_administrations = [] # Create a list for adding new administration objects
        test_period = int(study_obj.test_period)

        max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max'] 
        if max_subject_id is None: # If there is no max subject ID number (study has 0 participants)
            max_subject_id = 0 # Mark the max as 0
        for sid in range(max_subject_id+1, max_subject_id+autogenerate_count+1): 
            new_hash = random_url_generator() # Generate a unique hash ID
            new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = 1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=test_period))) # Create a new administration object and add to list

        administration.objects.bulk_create(new_administrations)
        new_administrations = administration.objects.filter(study = study_obj, subject_id__in = range(max_subject_id+1, max_subject_id+autogenerate_count+1))

        item_set = model_map(study_obj.instrument.name).objects.filter(item_type = 'word').values_list('itemID',flat=True)
        for admin_obj in new_administrations:
            BackgroundInfo.objects.update_or_create(administration = admin_obj, 
            age = np.random.choice(range(study_obj.instrument.min_age, study_obj.instrument.max_age+1),size = 1)[0], 
            sex = np.random.choice(['M','F','O'],size = 1, p = [0.49,0.49,0.02])[0], 
            birth_order = np.random.choice(range(1,10), size = 1),
            multi_birth_boolean = 0, birth_weight = 6.5,
            born_on_due_date = 0, mother_education = np.random.choice(range(9,20),size = 1)[0],
            father_education = np.random.choice(range(9,20),size = 1)[0],
            mother_yob = 1985, father_yob = 1985, annual_income = '50000-75000', caregiver_info = 2,
            other_languages_boolean = 0, ear_infections_boolean = 0, hearing_loss_boolean = 0, vision_problems_boolean = 0, 
            illnesses_boolean = 0, services_boolean = 0, worried_boolean = 0, learning_disability_boolean = 0)
            answered_items = np.random.choice(item_set, replace = False, size = len(item_set)/2)
            produced_words = []
            understood_words = []
            if study_obj.instrument.form == 'WS':
                produced_items = answered_items
                understood_items = None
            elif study_obj.instrument.form == 'WG':
                produced_items = np.random.choice(answered_items, replace = False, size = len(answered_items)/2)
                understood_items = list(set(answered_items) - set(produced_items))
            for word in produced_items:
                produced_words.append(administration_data(administration = admin_obj, item_ID = word, value = 'produces'))
            administration_data.objects.bulk_create(produced_words)
            if understood_items:
                for word in understood_items:
                    understood_words.append(administration_data(administration = admin_obj, item_ID = word, value = 'understands'))
                administration_data.objects.bulk_create(understood_words)

        new_administrations.update(completedBackgroundInfo = True, completed = True)

    def test_parent_UI(self):

        test_url = reverse('administer_new_parent', args=[self.study_obj.researcher, self.study_obj.name])
        self.open(test_url)

        try:
            self.wd.wait_for_css('#okaybtn',5).click()
        except NoSuchElementException:
            pass

        self.wd.execute_script('fastforward()')
        self.wd.wait_for_css('input[name="btn-next"]',5)[0].click()

        self.wd.execute_script('fastforward()')

        self.wd.wait_for_css('.submit-button')[0].click()

