import datetime
import logging
import random
import time

import numpy as np
import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models import Max
from django.test import LiveServerTestCase, tag
from django.test.utils import override_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from brookes.models import BrookesCode
from cdi_forms.models import BackgroundInfo, Instrument_Forms
from researcher_UI.models import (Administration, Instrument, InstrumentFamily,
                                  Study, administration_data)
from researcher_UI.utils.random_url_generator import random_url_generator

logger = logging.getLogger("selenium")
logger.setLevel(logging.ERROR)

# Create your tests here.


def generate_fake_results(study_obj, autogenerate_count):
    new_administrations = []  # Create a list for adding new administration objects
    test_period = int(study_obj.test_period)

    max_subject_id = Administration.objects.filter(study=study_obj).aggregate(
        Max("subject_id")
    )["subject_id__max"]
    if (
        max_subject_id is None
    ):  # If there is no max subject ID number (study has 0 participants)
        max_subject_id = 0  # Mark the max as 0
    for sid in range(max_subject_id + 1, max_subject_id + autogenerate_count + 1):
        new_hash = random_url_generator()  # Generate a unique hash ID
        new_administrations.append(
            Administration(
                study=study_obj,
                subject_id=sid,
                repeat_num=1,
                url_hash=new_hash,
                completed=False,
                due_date=(
                    datetime.datetime.now() + datetime.timedelta(days=test_period)
                ).replace(tzinfo=pytz.utc),
            )
        )  # Create a new administration object and add to list

    Administration.objects.bulk_create(new_administrations)
    new_administrations = Administration.objects.filter(
        study=study_obj,
        subject_id__in=range(
            max_subject_id + 1, max_subject_id + autogenerate_count + 1
        ),
    )

    instrument_obj = Instrument.objects.get(name=study_obj.instrument.name)
    cdi_items = Instrument_Forms.objects.filter(instrument=instrument_obj).order_by(
        "item_order"
    )
    item_set = cdi_items.values_list("itemID", flat=True)
    for admin_obj in new_administrations:
        BackgroundInfo.objects.update_or_create(
            administration=admin_obj,
            age=np.random.choice(
                range(study_obj.instrument.min_age, study_obj.instrument.max_age + 1),
                size=1,
            )[0],
            sex=np.random.choice(["M", "F", "O"], size=1, p=[0.49, 0.49, 0.02])[0],
            birth_order=np.random.choice(range(1, 10), size=1),
            multi_birth_boolean=0,
            birth_weight_lb=6.5,
            born_on_due_date=0,
            mother_education=np.random.choice(range(9, 20), size=1)[0],
            father_education=np.random.choice(range(9, 20), size=1)[0],
            mother_yob=1985,
            father_yob=1985,
            annual_income="50000-75000",
            caregiver_info=2,
            other_languages_boolean=0,
            ear_infections_boolean=0,
            hearing_loss_boolean=0,
            vision_problems_boolean=0,
            illnesses_boolean=0,
            services_boolean=0,
            worried_boolean=0,
            learning_disability_boolean=0,
        )
        answered_items = np.random.choice(
            cdi_items, replace=False, size=int(len(cdi_items) / 2)
        )
        answers = []
        for word in answered_items:
            try:
                answers.append(
                    administration_data(
                        administration=admin_obj,
                        item_ID=word.itemID,
                        value=random.choice(
                            [i.strip() for i in word.choices.choice_set.split(";")]
                        ),
                    )
                )
            except:
                pass
        administration_data.objects.bulk_create(answers)

    new_administrations.update(
        completedBackgroundInfo=True, completedSurvey=True, completed=True
    )
    call_command("crontab_scoring")


@tag("selenium", "researcher")
@override_settings(DEBUG=True)
class Reseacher_UIProcessTests(LiveServerTestCase):
    LiveServerTestCase.host = "web"
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.admin = User.objects.create_user(
            username="JohnLennon", password="JohnLennon"
        )
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()
        user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )
        user.is_active = True
        user.researcher.institution = "Test Institution"
        user.researcher.position = "Test Position"
        user.save()
        self.researcher = user

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.selenium = webdriver.Remote("http://selenium:4444", options=options)
        cls.selenium.implicitly_wait(1)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def researcher_login(self):
        self.selenium.get(f"{self.live_server_url}/accounts/login/")
        username_input = self.selenium.find_element("name", "username")
        username_input.send_keys(self.researcher.username)
        password_input = self.selenium.find_element("name", "password")
        password_input.send_keys("PaulMcCartney")
        self.selenium.find_element("name", "login").click()

    def set_researcher_instruments(self):
        for fam in InstrumentFamily.objects.all():
            self.researcher.researcher.allowed_instrument_families.add(fam)
            if fam.chargeable:
                bc = BrookesCode(
                    researcher=self.researcher,
                    instrument_family=fam,
                    applied=pytz.utc.localize(datetime.datetime.now()),
                )
                bc.save()
        for inst in Instrument.objects.all():
            self.researcher.researcher.allowed_instruments.add(inst)

    def researcher_login_plus_instruments(self):
        self.researcher_login()
        self.set_researcher_instruments()

    def create_new_study(self, study_name, study_instrument):
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        ).click()

        # fill in the form
        study_name_input = self.selenium.find_element("id", "id_name")
        study_name_input.send_keys(study_name)
        instrument_input = Select(self.selenium.find_element("id", "id_instrument"))
        instrument_input.select_by_value(study_instrument)
        self.selenium.find_element("id", "submit-id-submit").click()

    def test_researcher_login_to_researcher_UI(self):
        self.researcher_login()
        url = self.selenium.current_url.split(":")[2][5:]
        self.assertEqual("/interface/", url)

    def test_access_add_instrument_family(self):
        self.researcher_login()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_add_instruments']"))
        ).click()
        # Check Accessed Page
        self.assertIn(self.selenium.title, "WebCDI Interface: Add Instruments")

    def test_add_non_chargeable_instrument_family(self):
        self.researcher_login()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_add_instruments']"))
        ).click()
        instrument_family = InstrumentFamily.objects.filter(chargeable=False).order_by(
            "?"
        )[0]
        self.selenium.find_element(
            By.XPATH, f"//input[@value='{instrument_family.id}']"
        ).click()
        self.selenium.find_element(By.ID, "id_save").click()
        self.assertEqual(
            instrument_family.id,
            self.researcher.researcher.allowed_instrument_families.all()[0].id,
        )
        self.assertEqual(
            list(self.researcher.researcher.allowed_instruments.all()),
            list(Instrument.objects.filter(family=instrument_family)),
        )

    def test_add_chargeable_instrument_family(self):
        self.researcher_login()

        # create a brokes code
        code = BrookesCode()
        code.save()

        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_add_instruments']"))
        ).click()
        instrument_family = InstrumentFamily.objects.filter(chargeable=True).order_by(
            "?"
        )[0]
        self.selenium.find_element(
            By.XPATH, f"//input[@value='{instrument_family.id}']"
        ).click()
        self.selenium.find_element(By.ID, "id_save").click()

        # check at Brookes Code page
        self.assertIn(self.selenium.title, "WebCDI Interface: Add Code")
        code_input = self.selenium.find_element(By.ID, "id_code")
        code_input.send_keys(code.code)
        self.selenium.find_element(By.XPATH, f"//input[@value='Save']").click()

        # check back to interface page
        url = self.selenium.current_url.split(":")[2][5:]
        self.assertEqual("/interface/", url)
        self.assertEqual(
            instrument_family.id,
            self.researcher.researcher.allowed_instrument_families.all()[0].id,
        )
        self.assertEqual(
            list(self.researcher.researcher.allowed_instruments.all()),
            list(Instrument.objects.filter(family=instrument_family)),
        )
        self.assertEqual(BrookesCode.objects.all()[0].researcher.id, self.researcher.id)

    def test_access_to_add_study(self):
        self.researcher_login()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        ).click()
        self.assertIn(self.selenium.title, "WebCDI Interface: Add Study")
        title = self.selenium.find_element("id", "modal-title")
        self.assertIn(title.text, "Add new study")

    def test_add_new_study(self):
        self.researcher_login_plus_instruments()
        # check new study opens
        study_name = "Test Study"
        # delete study if it exists
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        self.assertEqual(
            1,
            Study.objects.filter(name=study_name, instrument=study_instrument).count(),
        )

    def test_add_participants_by_subject_id(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Add Participant By Subject Id Test"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # add participants using subject ids
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )

        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )

        new_subject_ids = self.selenium.find_element(By.ID, "new-subject-ids")
        new_subject_ids.send_keys("1, 2, 3")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        time.sleep(1)
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(3, len(administration_objs))

    # TODO
    #    Check Expired Brookes functionality

    def test_add_participants_by_autogenerate_id(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Add Participant By Autogenerate Id Test"
        study_instrument = Instrument.objects.all().order_by("?")[0].name

        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # add participants using autogenerate ids
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )
        new_subject_ids = self.selenium.find_element(By.ID, "autogenerate-count")
        new_subject_ids.send_keys("10")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(10, len(administration_objs))

    def test_add_participants_by_file_with_header(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Add Participant By File with Header Test"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # add participants using file with header
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = (
            settings.BASE_DIR + "/researcher_UI/fixtures/TestUploadIdsExample.csv"
        )
        new_subject_ids.send_keys(filename)
        csv_header = (
            WebDriverWait(self.selenium, 10)
            .until(EC.presence_of_element_located((By.ID, "csv-header")))
            .click()
        )
        csv_header = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-column"))
        )
        csv_header.send_keys("id")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(4, len(administration_objs))

    def test_add_participants_by_file_without_header(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Add Participant By File with Header Test"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # add participants using file without header
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = (
            settings.BASE_DIR
            + "/researcher_UI/fixtures/TestUploadIdsNoHeaderExample.csv"
        )
        new_subject_ids.send_keys(filename)
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(4, len(administration_objs))

    def test_add_participants_by_single_reusable_link(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Add Participant By Single Reusable Link"
        study_instrument = (
            Instrument.objects.filter(form__in=["WS", "WG", "L1", "L2A", "L2B", "CDI3"])
            .order_by("?")[0]
            .name
        )
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # add participants using single reusable link - this is done last because page changes
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )

        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "reusable_link"))
        ).click()

        url = self.selenium.current_url.split(":")[2][5:][:17]
        self.assertEqual("/form/background/", url)

        # TODO
        # complete background information form and check it exits
        # administration_objs = Administration.objects.filter(study=study_obj)
        # self.assertEqual(1, len(administration_objs))

    def test_add_participants_by_single_reusable_link_CAT(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Add Participant By Single Reusable Link"
        study_instrument = Instrument.objects.filter(form="CAT").order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # add participants using single reusable link - this is done last because page changes
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )

        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "reusable_link"))
        ).click()

        url = self.selenium.current_url.split(":")[2][5:][:17]
        self.assertEqual("/form/cat/backgro", url)

        # TODO
        # complete background information form and check it exits
        # administration_objs = Administration.objects.filter(study=study_obj)
        # self.assertEqual(1, len(administration_objs))

    def test_download_data(self):
        """
        Note: you need to manually check these are downloaded
        """
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Download Data"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        administration_objs = Administration.objects.filter(study=study_obj)

        # now clicked download data dropdown
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))
        ).click()
        # and the download button
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='download-study-csv']"))
        ).click()

        # download summary data
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='download-summary-csv']")
            )
        ).click()

        # download adjusted scoring format
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='download-study-csv-adjusted']")
            )
        ).click()

    def test_add_participants(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Add Participant Test"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # add participants using subject ids
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )
        new_subject_ids = self.selenium.find_element(By.ID, "new-subject-ids")
        new_subject_ids.send_keys("1, 2, 3")
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, "id_modal_submit_btn"))
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        time.sleep(1)
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(3, len(administration_objs))

        # add participants using autogenerate ids
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )
        new_subject_ids = self.selenium.find_element(By.ID, "autogenerate-count")
        new_subject_ids.send_keys("10")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(13, len(administration_objs))

        # add participants using file with header
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = (
            settings.BASE_DIR + "/researcher_UI/fixtures/TestUploadIdsExample.csv"
        )
        new_subject_ids.send_keys(filename)
        csv_header = (
            WebDriverWait(self.selenium, 10)
            .until(EC.presence_of_element_located((By.ID, "csv-header")))
            .click()
        )
        csv_header = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-column"))
        )
        csv_header.send_keys("id")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(17, len(administration_objs))

        # add participants using file without header
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = (
            settings.BASE_DIR
            + "/researcher_UI/fixtures/TestUploadIdsNoHeaderExample.csv"
        )
        new_subject_ids.send_keys(filename)
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(21, len(administration_objs))

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(31, len(administration_objs))

        # now clicked download data dropdown
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))
        ).click()
        # and the download button
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='download-study-csv']"))
        ).click()

        # download summary data
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='download-summary-csv']")
            )
        ).click()

        # add participants using single reusable link - this is done last because page changes
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='id_add_participants']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "modal-title"))
        )
        self.assertEqual(
            "Administer new subjects",
            self.selenium.find_element(By.ID, "modal-title").text,
        )
        new_subject_ids = (
            WebDriverWait(self.selenium, 10)
            .until(EC.presence_of_element_located((By.ID, "reusable_link")))
            .click()
        )

        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(31, len(administration_objs))

    def test_generate_results_for_all_instruments(self):
        # TODO Need a CAT equivalent
        self.researcher_login_plus_instruments()

        instruments = Instrument.objects.filter(
            form__in=["WS", "WG", "L1", "L2A", "L2B", "CDI3"]
        )
        for instrument_obj in instruments:
            # create new study
            study_name = "Generate Results All Studies - " + instrument_obj.name
            self.create_new_study(study_name, instrument_obj.name)
            # allow page to reload
            time.sleep(1)
            WebDriverWait(self.selenium, 100).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
            )
            study_obj = Study.objects.get(name=study_name)

            generate_fake_results(study_obj, 10)
            time.sleep(1)
            administration_objs = Administration.objects.filter(study=study_obj)
            self.assertEqual(10, len(administration_objs))
            WebDriverWait(self.selenium, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@id='dropdownMenu2']"))
            ).click()
            WebDriverWait(self.selenium, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@id='download-study-csv']")
                )
            ).click()

    def test_update_study(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Update Study Test"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # Test can update study
        self.selenium.get(
            f"{self.live_server_url}/interface/study/{study_obj.id}/detail/"
        )
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_update_study']"))
        ).click()
        time.sleep(1)
        days_to_expire = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "id_test_period"))
        )
        days_to_expire.clear()
        days_to_expire.send_keys("10")
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "submit-id-submit"))
        ).click()
        time.sleep(1)
        study_obj = Study.objects.get(name=study_name)
        self.assertEqual(10, study_obj.test_period)

    def test_delete_study(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Delete Study Test"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        # Test can delete study - this isn't the best way to do it but given the structure best I can think of ...
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@id='delete-study']"))
        ).click()
        alert = self.selenium.switch_to.alert.accept()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        try:
            study_obj = Study.objects.get(name=study_name)
            self.assertEqual(True, False)
        except:
            self.assertEqual(True, True)

    def test_select_all(self):
        self.researcher_login_plus_instruments()

        # create new study
        study_name = "Select Functionality"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        self.selenium.refresh()

        # ensure all checked
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@onclick='toggle(this)']"))
        ).click()
        els = self.selenium.find_elements(By.XPATH, "//input[@type='checkbox']")
        checked = True
        for el in els:
            if not el.is_selected():
                checked = False
                break
        self.assertEqual(True, checked)

        # ensure re-administer etc are selectable
        add_selected = self.selenium.find_element(By.ID, "add-selected")
        self.assertEqual(True, add_selected.is_enabled())
        download_selected = self.selenium.find_element(By.ID, "dropdownMenu")
        self.assertEqual(True, download_selected.is_enabled())
        delete_selected = self.selenium.find_element(By.ID, "delete-selected")
        self.assertEqual(True, delete_selected.is_enabled())

        # ensure none checked
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@onclick='toggle(this)']"))
        ).click()
        els = self.selenium.find_elements(By.XPATH, "//input[@type='checkbox']")
        checked = True
        for el in els:
            if el.is_selected():
                checked = False
                break
        self.assertEqual(True, checked)

        # ensure re-administer etc are NOT selectable
        self.assertEqual(False, add_selected.is_enabled())
        self.assertEqual(False, download_selected.is_enabled())
        self.assertEqual(False, delete_selected.is_enabled())

    def test_readminister(self):
        self.researcher_login_plus_instruments()

        # create new study
        study_name = "Readminister Functionality"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        self.selenium.refresh()

        # ensure all checked
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@onclick='toggle(this)']"))
        ).click()
        els = self.selenium.find_elements(By.XPATH, "//input[@type='checkbox']")

        self.selenium.find_element(By.ID, "add-selected").click()

        self.selenium.refresh()
        els = self.selenium.find_elements(By.XPATH, "//input[@type='checkbox']")

        self.assertEqual(21, len(els))

    def test_download_selected(self):
        self.researcher_login_plus_instruments()
        # create new study
        study_name = "Download Selected Functionality"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        self.selenium.refresh()

        # check every other element
        els = self.selenium.find_elements(By.XPATH, "//input[@type='checkbox']")
        count = 2
        for el in els:
            count += 1
            if count % 2 == 0:
                el.click()

        self.selenium.find_element(By.ID, "dropdownMenu").click()
        self.selenium.find_element(By.ID, "download-selected").click()

        self.selenium.find_element(By.ID, "dropdownMenu").click()
        self.selenium.find_element(By.ID, "download-selected-summary").click()

        self.selenium.find_element(By.ID, "dropdownMenu").click()
        self.selenium.find_element(By.ID, "download-links").click()

    def test_delete_selected(self):
        self.researcher_login_plus_instruments()
        # create new study
        study_name = "Delete Selected Functionality"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        study_obj = Study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        self.selenium.refresh()

        # check every other element
        els = self.selenium.find_elements(By.XPATH, "//input[@type='checkbox']")
        count = 2
        for el in els:
            count += 1
            if count % 2 == 0:
                el.click()

        self.selenium.find_element(By.ID, "delete-selected").click()
        alert = self.selenium.switch_to.alert.accept()
        time.sleep(5)
        administration_objs = Administration.objects.filter(
            study=study_obj, is_active=True
        )
        self.assertEqual(5, len(administration_objs))
