import csv
import datetime
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.cat_forms.forms import CatItemForm
from cdi_forms.models import BackgroundInfo
from researcher_UI.models import Administration, Instrument, Study
from researcher_UI.tests.utils import random_password


def csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [cell for cell in row]


def make_boolean(text):
    if text == "1":
        return True
    return False


class CATSpanishAdministrationDataItemTest(TestCase):
    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="secret")

        instrument = Instrument.objects.get(
            language="Spanish",
            form="CAT",
        )

        self.study = Study.objects.create(
            researcher=self.user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )
        self.hash = random_password(size=64)
        self.administration = Administration.objects.create(
            study=self.study,
            subject_id=1,
            repeat_num=1,
            url_hash=self.hash,
            completed=False,
            due_date=timezone.now() + datetime.timedelta(days=31),
            completedBackgroundInfo=True,
        )

        self.backgroundinfo = BackgroundInfo.objects.create(
            administration=self.administration, age=13, source_id=random_password()
        )

        self.url = reverse(
            "cat_forms:administer_cat_form",
            kwargs={"hash_id": self.administration.url_hash},
        )

    def start_values(self, file_name):
        for age in range(12, 37):
            # read csv, and split on "," the line
            csv_file = csv.reader(open(os.path.realpath(file_name), "r"), delimiter=",")
            # loop through the csv list
            for row in csv_file:
                # if current rows 2nd value is equal to input, print that row
                if str(age) == row[0]:
                    word = row[4]
            self.backgroundinfo.age = age
            self.backgroundinfo.save()

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.context["form"], CatItemForm)
            self.assertContains(response, f"¿Su hijo/a dice ...{word} ?")

    def sequence_test(self, file_name):
        response = self.client.get(self.url)

        contents = list(
            csv_reader(
                open(
                    os.path.realpath(file_name),
                    encoding="utf8",
                )
            )
        )
        col_names = contents[0]
        for row in contents[1:]:
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.context["form"], CatItemForm)
            self.assertContains(
                response, f"¿Su hijo/a dice ...{row[col_names.index('item')]}?"
            )
            payload = {
                "word_id": row[col_names.index("index")],
                "label": row[col_names.index("item")],
                "item": make_boolean(row[col_names.index("response")]),
            }
            if make_boolean(row[col_names.index("response")]):
                payload["yes"] = True
            else:
                payload["no"] = True
            response = self.client.post(self.url, payload)
            if row == contents[-1]:
                response = self.client.get(self.url)
                response = self.client.get(self.url)
                self.assertTrue(response.context["object"].scored)
            else:
                self.assertRedirects(
                    response,
                    self.url,
                )
                response = self.client.get(self.url)
                self.assertEqual(
                    response.context["object"].catresponse.est_theta,
                    float("{:.4f}".format(float(row[col_names.index("theta")]))),
                )

    def test_spanish_start_values(self):
        self.start_values(
            f"{settings.BASE_DIR}/cdi_forms/cat_forms/tests/test_data/spanish_start.csv"
        )

    def test_spanish_seq_1(self):
        self.sequence_test(
            f"{settings.BASE_DIR}/cdi_forms/cat_forms/tests/test_data/spanish_sequence_1.csv"
        )

    def test_spanish_seq_2(self):
        self.backgroundinfo.age = 24
        self.backgroundinfo.save()
        self.sequence_test(
            f"{settings.BASE_DIR}/cdi_forms/cat_forms/tests/test_data/spanish_sequence_2.csv"
        )
