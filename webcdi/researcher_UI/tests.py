from django.test import TestCase

from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from django.contrib.auth.models import User
from django.urls import reverse
import pickle, time, datetime, random

from django.conf import settings
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC

from django.core.management import call_command
from django.db.models import Max
from django.test.utils import override_settings
from .models.models import study, researcher, instrument, administration, administration_data
from .views import random_url_generator
from cdi_forms.models import BackgroundInfo, Instrument_Forms
from cdi_forms.views import model_map
import numpy as np

# Create your tests here.

def generate_fake_results(study_obj, autogenerate_count):
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

    #item_set = model_map(study_obj.instrument.name).filter(item_type = 'word').values_list('itemID',flat=True)
    instrument_obj = instrument.objects.get(name=study_obj.instrument.name)
    cdi_items = Instrument_Forms.objects.filter(instrument=instrument_obj).order_by('item_order')
    item_set = cdi_items.values_list('itemID', flat=True)
    for admin_obj in new_administrations:
        BackgroundInfo.objects.update_or_create(administration = admin_obj, 
        age = np.random.choice(range(study_obj.instrument.min_age, study_obj.instrument.max_age+1),size = 1)[0], 
        sex = np.random.choice(['M','F','O'],size = 1, p = [0.49,0.49,0.02])[0], 
        birth_order = np.random.choice(range(1,10), size = 1),
        multi_birth_boolean = 0, birth_weight_lb = 6.5,
        born_on_due_date = 0, mother_education = np.random.choice(range(9,20),size = 1)[0],
        father_education = np.random.choice(range(9,20),size = 1)[0],
        mother_yob = 1985, father_yob = 1985, annual_income = '50000-75000', caregiver_info = 2,
        other_languages_boolean = 0, ear_infections_boolean = 0, hearing_loss_boolean = 0, vision_problems_boolean = 0, 
        illnesses_boolean = 0, services_boolean = 0, worried_boolean = 0, learning_disability_boolean = 0)
        answered_items = np.random.choice(cdi_items, replace=False, size=int(len(cdi_items)/2))
        answers = []
        for word in answered_items:
            try: answers.append(administration_data(administration=admin_obj, item_ID=word.itemID, value=random.choice([i.strip() for i in word.choices.choice_set.split(';')])))
            except: pass
        administration_data.objects.bulk_create(answers)
        
    new_administrations.update(completedBackgroundInfo = True, completedSurvey=True, completed = True)

@override_settings(DEBUG=True)
class MySeleniumTests(LiveServerTestCase):
    fixtures = ['researcher_UI/fixtures/instrument-fixtures.json','cdi_forms/fixtures/choices.json','researcher_UI/fixtures/scoring.json',
        'researcher_UI/fixtures/benchmark.json']

    def setUp(self):
        self.admin = User.objects.create_user(username='JohnLennon', password = 'JohnLennon')
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()
        user = User.objects.create_user(username='PaulMcCartney', password = 'PaulMcCartney')
        self.researcher = researcher (
            user = user,
            institution = "Test Institution",
            position = "Test Position"
        )
        self.researcher.save()
        instruments = instrument.objects.all()
        for inst in instruments: self.researcher.allowed_instruments.add(instrument.objects.get(name=inst.name))
       
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

    def researcher_login(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/interface/'))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.researcher.user.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys("PaulMcCartney")
        self.selenium.find_element_by_id('id_log_in').click()

    def create_new_study(self, study_name, study_instrument):
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        
        #fill in the form
        study_name_input = self.selenium.find_element_by_id("id_name")
        study_name_input.send_keys(study_name)
        instrument_input = Select(self.selenium.find_element_by_id("id_instrument"))
        instrument_input.select_by_value(study_instrument)
        self.selenium.find_element_by_id("id_add_study_modal_submit").click()

    def test_researcher_login_to_researchUI(self):
        self.researcher_login()
        url = self.selenium.current_url.split(':')[2][5:]
        self.assertEqual(u'/interface/', url)

    def test_new_study(self):
        self.researcher_login()

        # check new study opens
        study_name = "Test Study"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)
        self.assertEqual(1, study.objects.filter(name=study_name).count())
            
    def test_add_participants_by_subject_id(self):
        self.researcher_login()

        # check new study opens
        study_name = "Add Participant By Subject Id Test"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)
        
        # add participants using subject ids
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = self.selenium.find_element_by_id("new-subject-ids")
        new_subject_ids.send_keys("1, 2, 3")
        self.selenium.find_element_by_id("id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        time.sleep(1)
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(3, len(administration_objs))

    def test_add_participants_by_autogenerate_id(self):
        self.researcher_login()

        # check new study opens
        study_name = "Add Participant By Autogenerate Id Test"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        # add participants using autogenerate ids
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = self.selenium.find_element_by_id("autogenerate-count")
        new_subject_ids.send_keys("10")
        self.selenium.find_element_by_id("id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        time.sleep(1) # this is here because sometimes all records aren't being saved
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(10, len(administration_objs))


    def test_add_participants_by_file_with_header(self):
        self.researcher_login()

        # check new study opens
        study_name = "Add Participant By File with Header Test"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        # add participants using file with header
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = settings.BASE_DIR + "/researcher_UI/fixtures/TestUploadIdsExample.csv"
        new_subject_ids.send_keys(filename)
        csv_header = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "csv-header"))
        ).click()
        csv_header = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-column"))
        )
        csv_header.send_keys("id")
        self.selenium.find_element_by_id("id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        time.sleep(1) # this is here because sometimes all records aren't being saved
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(4, len(administration_objs))

    def test_add_participants_by_file_without_header(self):
        self.researcher_login()

        # check new study opens
        study_name = "Add Participant By File with Header Test"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        # add participants using file without header
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = settings.BASE_DIR + "/researcher_UI/fixtures/TestUploadIdsNoHeaderExample.csv"
        new_subject_ids.send_keys(filename)
        self.selenium.find_element_by_id("id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        time.sleep(1) # this is here because sometimes all records aren't being saved
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(4, len(administration_objs))

    def test_add_participants_by_single_reusable_link(self):
        self.researcher_login()

        # check new study opens
        study_name = "Add Participant By Single Reusable Link"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        # add participants using single reusable link - this is done last because page changes
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "reusable_link"))).click()

        url = self.selenium.current_url.split(':')[2][5:][:17] 
        self.assertEqual(u'/form/background/', url)
        
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(1, len(administration_objs))

    def test_download_data(self):
        '''
        Note: you need to manually check these are downloaded
        '''
        call_command('populate_items')
        self.researcher_login()

        # check new study opens
        study_name = "Download Data"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        administration_objs = administration.objects.filter(study=study_obj)

        #now clicked download data dropdown
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
        # and the download button
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-study-csv']"))).click()
        
        #download summary data
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-summary-csv']"))).click()
        
        #download CDI scoring format
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-study-scoring']"))).click()
        
        #download dictionary
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-dictionary']"))).click()


    def test_add_participants(self):
        call_command('populate_items')
        self.researcher_login()

        # check new study opens
        study_name = "Add Participant Test"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)
        
        # add participants using subject ids
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = self.selenium.find_element_by_id("new-subject-ids")
        new_subject_ids.send_keys("1, 2, 3")
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.ID, "id_modal_submit_btn"))).click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        time.sleep(1)
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(3, len(administration_objs))

        # add participants using autogenerate ids
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = self.selenium.find_element_by_id("autogenerate-count")
        new_subject_ids.send_keys("10")
        self.selenium.find_element_by_id("id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        time.sleep(1) # this is here because sometimes all records aren't being saved
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(13, len(administration_objs))

        # add participants using file with header
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = settings.BASE_DIR + "/researcher_UI/fixtures/TestUploadIdsExample.csv"
        new_subject_ids.send_keys(filename)
        csv_header = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "csv-header"))
        ).click()
        csv_header = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-column"))
        )
        csv_header.send_keys("id")
        self.selenium.find_element_by_id("id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        time.sleep(1) # this is here because sometimes all records aren't being saved
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(17, len(administration_objs))

        # add participants using file without header
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = settings.BASE_DIR + "/researcher_UI/fixtures/TestUploadIdsNoHeaderExample.csv"
        new_subject_ids.send_keys(filename)
        self.selenium.find_element_by_id("id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        time.sleep(1) # this is here because sometimes all records aren't being saved
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(21, len(administration_objs))

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(31, len(administration_objs))

        #now clicked download data dropdown
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
        # and the download button
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-study-csv']"))).click()
        
        #download summary data
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-summary-csv']"))).click()
        
        #download CDI scoring format
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-study-scoring']"))).click()
        
        #download dictionary
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-dictionary']"))).click()
        
        # add participants using single reusable link - this is done last because page changes
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_add_participants']"))).click()
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "modal-title")))
        self.assertEqual(u'Administer new subjects', self.selenium.find_element_by_id("modal-title").text)
        new_subject_ids = WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "reusable_link"))).click()

        url = self.selenium.current_url.split(':')[2][5:][:17] 
        self.assertEqual(u'/form/background/', url)
        
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(32, len(administration_objs))

    def test_generate_results_for_all_instruments(self):
        call_command('populate_items')
        self.researcher_login()

        instruments = instrument.objects.all()
        for instrument_obj in instruments:
        # create new study 
            study_name = "Generate Results All Studies - " + instrument_obj.name
            self.create_new_study(study_name, instrument_obj.name)
            # allow page to reload
            time.sleep(1)
            WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
            study_obj = study.objects.get(name=study_name)

            generate_fake_results(study_obj, 10)
            time.sleep(1)
            administration_objs = administration.objects.filter(study=study_obj)
            self.assertEqual(10, len(administration_objs))
            WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))).click()
            WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='download-study-csv']"))).click()

    def test_update_study(self):
        self.researcher_login()

        # check new study opens
        study_name = "Update Study Test"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)
        
        # Test can update study
        self.selenium.get('%s%s' % (self.live_server_url, '/interface/'))
        study_input = Select(self.selenium.find_element_by_id("study-selector"))
        study_input.select_by_value('/interface/study/' + study_name + '/')
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_update_study']"))).click()
        time.sleep(1)
        days_to_expire =  WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "id_test_period")))
        days_to_expire.clear()
        days_to_expire.send_keys("10")
        WebDriverWait(self.selenium, 10).until(EC.presence_of_element_located((By.ID, "id_add_study_modal_submit"))).click()
        time.sleep(1)
        study_obj = study.objects.get(name=study_name)
        self.assertEqual(10, study_obj.test_period)

    def test_delete_study(self):
        self.researcher_login()

        # check new study opens
        study_name = "Delete Study Test"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        # Test can delete study - this isn't the best way to do it but given the structure best I can think of ...
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='delete-study']"))).click()
        alert = self.selenium.switch_to_alert()
        alert.accept()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        try:
            study_obj = study.objects.get(name=study_name)
            self.assertEqual(True, False)
        except:
            self.assertEqual(True, True)

    def test_select_all(self):
        call_command('populate_items')
        self.researcher_login()

        # create new study 
        study_name = "Select Functionality"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        self.selenium.refresh()

        # ensure all checked
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@onclick='toggle(this)']"))).click()
        els = self.selenium.find_elements_by_xpath("//input[@type='checkbox']")
        checked = True
        for el in els:
            if not el.is_selected(): 
                checked=False
                break
        self.assertEqual(True, checked)

        #ensure re-administer etc are selectable
        add_selected = self.selenium.find_element_by_id('add-selected')
        self.assertEqual(True, add_selected.is_enabled())
        download_selected = self.selenium.find_element_by_id('dropdownMenu')
        self.assertEqual(True, download_selected.is_enabled())
        delete_selected = self.selenium.find_element_by_id('delete-selected')
        self.assertEqual(True, delete_selected.is_enabled())

        #ensure none checked
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@onclick='toggle(this)']"))).click()
        els = self.selenium.find_elements_by_xpath("//input[@type='checkbox']")
        checked = True
        for el in els:
            if el.is_selected(): 
                checked=False
                break
        self.assertEqual(True, checked)

        #ensure re-administer etc are NOT selectable
        self.assertEqual(False, add_selected.is_enabled())
        self.assertEqual(False, download_selected.is_enabled())
        self.assertEqual(False, delete_selected.is_enabled())


    def test_readminister(self):
        call_command('populate_items')
        self.researcher_login()

        # create new study 
        study_name = "Readminister Functionality"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        self.selenium.refresh()

        # ensure all checked
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@onclick='toggle(this)']"))).click()
        els = self.selenium.find_elements_by_xpath("//input[@type='checkbox']")
        
        self.selenium.find_element_by_id('add-selected').click()

        self.selenium.refresh()
        els = self.selenium.find_elements_by_xpath("//input[@type='checkbox']")
        
        self.assertEqual(21, len(els))
        
    def test_download_selected(self):
        call_command('populate_items')
        self.researcher_login()
        # create new study 
        study_name = "Download Selected Functionality"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        self.selenium.refresh()

        #check every other element
        els = self.selenium.find_elements_by_xpath("//input[@type='checkbox']")
        count = 2
        for el in els:
            count += 1
            if count % 2 == 0:
                el.click()
        
        self.selenium.find_element_by_id('dropdownMenu').click()
        self.selenium.find_element_by_id('download-selected').click()

        self.selenium.find_element_by_id('dropdownMenu').click()
        self.selenium.find_element_by_id('download-selected-summary').click()
        
        self.selenium.find_element_by_id('dropdownMenu').click()
        self.selenium.find_element_by_id('download-links').click()
        
        self.selenium.find_element_by_id('dropdownMenu').click()
        self.selenium.find_element_by_id('download-study-scoring-selected').click()


    def test_delete_selected(self):
        call_command('populate_items')
        self.researcher_login()
        # create new study 
        study_name = "Delete Selected Functionality"
        study_instrument = instrument.objects.all().order_by('?')[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        study_obj = study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        self.selenium.refresh()

        #check every other element
        els = self.selenium.find_elements_by_xpath("//input[@type='checkbox']")
        count = 2
        for el in els:
            count += 1
            if count % 2 == 0:
                el.click()

        
        self.selenium.find_element_by_id('delete-selected').click()
        alert = self.selenium.switch_to_alert()
        alert.accept()
        WebDriverWait(self.selenium, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='id_new_study']")))
        administration_objs = administration.objects.filter(study=study_obj)
        self.assertEqual(5, len(administration_objs))