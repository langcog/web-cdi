
from django.test import TestCase, tag
from django.urls import reverse
from researcher_UI.models import Instrument, InstrumentFamily


class AjaxDemographicFormsTest(TestCase):
    def setUp(self):
        self.url = reverse("researcher_ui:get_demographic_forms")
        instrument_family = InstrumentFamily.objects.create(
            name="BigCats", chargeable=True
        )
        self.instrument = Instrument.objects.create(
            name="lion",
            language="lionish",
            form="roar",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        
    def test_get(self):
        payload = {
            'id': self.instrument.name
        }
        response = self.client.get(self.url, payload)
        self.assertEqual(response.status_code, 200)

    def test_get_invalid_insrument(self):
        payload = {
            'id': 'peanut'
        }
        response = self.client.get(self.url, payload)
        self.assertEqual(response.status_code, 200)

class AjaxChargeStatusTest(TestCase):
    def setUp(self):
        instrument_family = InstrumentFamily.objects.create(
            name="BigCats", chargeable=True
        )
        self.chargeable_instrument = Instrument.objects.create(
            name="lion",
            language="lionish",
            form="roar",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        instrument_family = InstrumentFamily.objects.create(
            name="SamllCats", chargeable=False
        )
        self.non_chargeable_instrument = Instrument.objects.create(
            name="tabby",
            language="tabbyish",
            form="meow",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        self.url = reverse("researcher_ui:get_charge_status")
        
    def test_get_chargeable_true(self):
        payload = {
            'id': self.chargeable_instrument.name
        }
        response = self.client.get(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["chargeable"], Instrument.objects.get(name=self.chargeable_instrument.name).family.chargeable
        )
        self.assertTrue(response.json()["chargeable"])

    def test_get_non_chargeable_true(self):
        payload = {
            'id': self.non_chargeable_instrument.name
        }
        response = self.client.get(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["chargeable"], Instrument.objects.get(name=self.non_chargeable_instrument.name).family.chargeable
        )
        self.assertFalse(response.json()["chargeable"])