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
from urllib.parse import urlparse
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
from researcher_UI.tests.utils import LiveServerFixturesMixin
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
            birth_order=np.random.choice(range(1, 10), size=1)[0],
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
class Reseacher_UIProcessTests(LiveServerFixturesMixin, LiveServerTestCase):
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
        # wide enough that the navbar isn't collapsed
        cls.selenium.set_window_size(1400, 1000)

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

    def path(self):
        return urlparse(self.selenium.current_url).path

    def wait_for_group_page(self, timeout=100):
        # the group page (after creating a group or adding administrations)
        WebDriverWait(self.selenium, timeout).until(
            EC.element_to_be_clickable((By.ID, "id_add_participants"))
        )

    def open_add_administrations(self, tab=None):
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, "id_add_participants"))
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element((By.ID, "modal-title"), "Add administrations")
        )
        if tab:
            WebDriverWait(self.selenium, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//a[@data-toggle='pill' and normalize-space()='{tab}']")
                )
            ).click()

    def download(self, name):
        # one Download menu; with rows ticked its items post the selected-rows names
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, "download-menu-btn"))
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[@name='{name}']"))
        ).click()

    def create_new_study(self, study_name, study_instrument):
        # "New administration group" is on the dashboard
        self.selenium.get(f"{self.live_server_url}/interface/")
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
        url = self.path()
        self.assertEqual("/interface/", url)

    def test_access_add_instrument_family(self):
        self.researcher_login()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Instruments"))
        ).click()
        # Check Accessed Page
        self.assertIn(self.selenium.title, "WebCDI Interface: Add Instruments")

    def test_add_non_chargeable_instrument_family(self):
        self.researcher_login()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Instruments"))
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
            EC.element_to_be_clickable((By.LINK_TEXT, "Instruments"))
        ).click()
        instrument_family = InstrumentFamily.objects.filter(chargeable=True).order_by(
            "?"
        )[0]
        self.selenium.find_element(
            By.XPATH, f"//input[@value='{instrument_family.id}']"
        ).click()
        self.selenium.find_element(By.ID, "id_save").click()

        # check at Brookes Code page
        self.assertEqual(self.selenium.title, "Web-CDI: Brookes access code")
        code_input = self.selenium.find_element(By.ID, "id_code")
        code_input.send_keys(code.code)
        self.selenium.find_element(
            By.XPATH, "//button[normalize-space()='Apply code']"
        ).click()

        # check back to interface page
        url = self.path()
        self.assertEqual("/interface/", url)
        self.assertEqual(
            instrument_family.id,
            self.researcher.researcher.allowed_instrument_families.all()[0].id,
        )
        self.assertEqual(
            list(self.researcher.researcher.allowed_instruments.all()),
            list(Instrument.objects.filter(family=instrument_family)),
        )
        # the fixtures have a code of their own; check the one applied here
        code.refresh_from_db()
        self.assertEqual(code.researcher_id, self.researcher.id)

    def test_access_to_add_study(self):
        self.researcher_login()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        ).click()
        self.assertEqual(self.selenium.title, "New administration group")
        title = self.selenium.find_element("id", "modal-title")
        self.assertEqual(title.text, "New administration group")

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
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        # add participants using subject ids
        self.open_add_administrations()

        new_subject_ids = self.selenium.find_element(By.ID, "new-subject-ids")
        new_subject_ids.send_keys("1, 2, 3")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        self.wait_for_group_page()
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
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        # add participants using autogenerate ids
        self.open_add_administrations("Generate IDs for me")
        # wait for the tab's fade-in before typing
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "autogenerate-count"))
        )
        new_subject_ids.send_keys("10")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        self.wait_for_group_page()
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
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        # add participants using file with header
        self.open_add_administrations("Upload a CSV of IDs")
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = (
            settings.BASE_DIR + "/researcher_UI/fixtures/TestUploadIdsExample.csv"
        )
        new_subject_ids.send_keys(filename)
        csv_header = (
            WebDriverWait(self.selenium, 10)
            .until(EC.element_to_be_clickable((By.ID, "csv-header")))
            .click()
        )
        csv_header = WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "subject-ids-column"))
        )
        csv_header.send_keys("id")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        self.wait_for_group_page()
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
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        # add participants using file without header
        self.open_add_administrations("Upload a CSV of IDs")
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = (
            settings.BASE_DIR
            + "/researcher_UI/fixtures/TestUploadIdsNoHeaderExample.csv"
        )
        new_subject_ids.send_keys(filename)
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        self.wait_for_group_page()
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
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        # add participants using single reusable link - this is done last because page changes
        self.open_add_administrations("Reusable link")

        # the dialog shows the reusable link to copy; follow it
        link = WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "reusable_link_input"))
        ).get_attribute("value")
        self.selenium.get(link)

        url = self.path()[:17]
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
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        # add participants using single reusable link - this is done last because page changes
        self.open_add_administrations("Reusable link")

        # the dialog shows the reusable link to copy; follow it
        link = WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "reusable_link_input"))
        ).get_attribute("value")
        self.selenium.get(link)

        url = self.path()[:17]
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
        # generate_fake_results writes item answers, not CAT responses
        study_instrument = (
            Instrument.objects.exclude(form__in=settings.CAT_FORMS)
            .order_by("?")[0]
            .name
        )
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        administration_objs = Administration.objects.filter(study=study_obj)

        # now clicked download data dropdown
        self.download("download-study-csv")

        # download summary data
        self.download("download-summary-csv")

        # download adjusted scoring format
        self.download("download-study-csv-adjusted")

    def test_add_participants(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Add Participant Test"
        # generate_fake_results writes item answers, not CAT responses
        study_instrument = (
            Instrument.objects.exclude(form__in=settings.CAT_FORMS)
            .order_by("?")[0]
            .name
        )
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        # add participants using subject ids
        self.open_add_administrations()
        new_subject_ids = self.selenium.find_element(By.ID, "new-subject-ids")
        new_subject_ids.send_keys("1, 2, 3")
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, "id_modal_submit_btn"))
        ).click()
        self.wait_for_group_page()
        time.sleep(1)
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(3, len(administration_objs))

        # add participants using autogenerate ids
        self.open_add_administrations("Generate IDs for me")
        # wait for the tab's fade-in before typing
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "autogenerate-count"))
        )
        new_subject_ids.send_keys("10")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        self.wait_for_group_page()
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(13, len(administration_objs))

        # add participants using file with header
        self.open_add_administrations("Upload a CSV of IDs")
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = (
            settings.BASE_DIR + "/researcher_UI/fixtures/TestUploadIdsExample.csv"
        )
        new_subject_ids.send_keys(filename)
        csv_header = (
            WebDriverWait(self.selenium, 10)
            .until(EC.element_to_be_clickable((By.ID, "csv-header")))
            .click()
        )
        csv_header = WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "subject-ids-column"))
        )
        csv_header.send_keys("id")
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        self.wait_for_group_page()
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(17, len(administration_objs))

        # add participants using file without header
        self.open_add_administrations("Upload a CSV of IDs")
        new_subject_ids = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "subject-ids-csv"))
        )
        filename = (
            settings.BASE_DIR
            + "/researcher_UI/fixtures/TestUploadIdsNoHeaderExample.csv"
        )
        new_subject_ids.send_keys(filename)
        self.selenium.find_element(By.ID, "id_modal_submit_btn").click()
        self.wait_for_group_page()
        time.sleep(1)  # this is here because sometimes all records aren't being saved
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(21, len(administration_objs))

        generate_fake_results(study_obj, 10)
        time.sleep(1)
        administration_objs = Administration.objects.filter(study=study_obj)
        self.assertEqual(31, len(administration_objs))

        # now clicked download data dropdown
        self.download("download-study-csv")

        # download summary data
        self.download("download-summary-csv")

        # add participants using single reusable link - this is done last because page changes
        self.open_add_administrations("Reusable link")
        # the dialog shows the reusable link to copy; follow it
        link = WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "reusable_link_input"))
        ).get_attribute("value")
        self.selenium.get(link)

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
            self.wait_for_group_page()
            study_obj = Study.objects.get(name=study_name)

            generate_fake_results(study_obj, 10)
            time.sleep(1)
            administration_objs = Administration.objects.filter(study=study_obj)
            self.assertEqual(10, len(administration_objs))
            self.download("download-study-csv")

    def test_update_study(self):
        self.researcher_login_plus_instruments()

        # check new study opens
        study_name = "Update Study Test"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        self.wait_for_group_page()
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
        self.wait_for_group_page()
        study_obj = Study.objects.get(name=study_name)

        # Group settings -> "Delete group..." -> type the group name to confirm
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, "id_update_study"))
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-target='#delete-group-modal']")
            )
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, "delete-group-confirm"))
        ).send_keys(study_name)
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, "delete-group-submit"))
        ).click()
        # back on the dashboard; deletes are soft
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='id_new_study']"))
        )
        self.assertFalse(Study.objects.get(pk=study_obj.pk).active)

    def test_select_all(self):
        self.researcher_login_plus_instruments()

        # create new study
        study_name = "Select Functionality"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        self.wait_for_group_page()
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

        # ensure re-administer etc are selectable, and downloads switch to
        # the selected rows
        add_selected = self.selenium.find_element(By.ID, "add-selected")
        self.assertEqual(True, add_selected.is_enabled())
        delete_selected = self.selenium.find_element(By.ID, "delete-selected-open")
        self.assertEqual(True, delete_selected.is_enabled())
        download_summary = self.selenium.find_element(
            By.XPATH, "//button[@data-all='download-summary-csv']"
        )
        self.assertEqual(
            "download-selected-summary", download_summary.get_attribute("name")
        )

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
        self.assertEqual(False, delete_selected.is_enabled())
        self.assertEqual(
            "download-summary-csv", download_summary.get_attribute("name")
        )

    def test_readminister(self):
        self.researcher_login_plus_instruments()

        # create new study
        study_name = "Readminister Functionality"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        self.wait_for_group_page()
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
        # generate_fake_results writes item answers, not CAT responses
        study_instrument = (
            Instrument.objects.exclude(form__in=settings.CAT_FORMS)
            .order_by("?")[0]
            .name
        )
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        self.wait_for_group_page()
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

        self.download("download-selected")
        self.download("download-selected-summary")
        self.download("download-links")

    def test_delete_selected(self):
        self.researcher_login_plus_instruments()
        # create new study
        study_name = "Delete Selected Functionality"
        study_instrument = Instrument.objects.all().order_by("?")[0].name
        self.create_new_study(study_name, study_instrument)
        # allow page to reload
        time.sleep(1)
        self.wait_for_group_page()
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

        self.selenium.find_element(By.ID, "delete-selected-open").click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, "delete-selected"))
        ).click()
        self.wait_for_group_page()
        time.sleep(1)
        administration_objs = Administration.objects.filter(
            study=study_obj, is_active=True
        )
        self.assertEqual(5, len(administration_objs))
