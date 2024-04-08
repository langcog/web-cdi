from django.test import Client, TestCase, tag
from django.urls import resolve

from brookes.views import *


class TestBrookesUrls(TestCase):
    def setUp(self):

        self.instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=True
        )

    def test_enter_codes_url(self):
        resolver = resolve(
            "brookes:enter_codes",
            kwargs={"intrument_family": self.instrument_family.id},
        )
        self.assertEqual(resolver.func.cls, UpdateBrookesCode)
