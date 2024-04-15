from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from brookes.forms import BrookesCodeForm
from brookes.models import BrookesCode
from researcher_UI.models import InstrumentFamily


@tag("model")
class BrookesCodeFormTest(TestCase):
    def setUp(self) -> None:
        self.brookes_code = BrookesCode.objects.create()
        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        self.instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=True
        )

    def test_valid_form(self):
        data = {
            "code": self.brookes_code.code,
            "cancel": "Save",
        }
        form = BrookesCodeForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        data = {
            "code": "UnlikelyCode",
            "cancel": "Save",
        }
        form = BrookesCodeForm(data=data)
        self.assertEqual(form.errors["code"][0], "Invalid code")

    def test_cancel_form(self):
        data = {
            "code": self.brookes_code.code,
            "cancel": "Cancel",
        }
        form = BrookesCodeForm(data=data)
        self.assertTrue(form.is_valid())

    def test_code_applied(self):
        x = BrookesCode.objects.create(
            instrument_family=self.instrument_family,
            researcher=self.user,
            applied=timezone.now(),
        )
        data = {
            "code": x.code,
            "cancel": "Save",
        }
        form = BrookesCodeForm(data=data)
        self.assertEqual(form.errors["code"][0], "Code already applied")
