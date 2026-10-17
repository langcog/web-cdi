import importlib
import json
import os

from django.apps import apps
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from cdi_forms.utils import PROJECT_ROOT
from researcher_UI.models import (Administration, Demographic, Instrument,
                                  InstrumentFamily, Study)

migration = importlib.import_module("cdi_forms.migrations.0096_fix_japanese_income_keys")


class JapaneseIncomeKeysTest(TestCase):
    """#665: three Japanese income answers were stored under wrong keys."""

    def test_form_keys_match_labels(self):
        path = os.path.join(PROJECT_ROOT, "form_data/background_info/Japanese_no_NIH.json")
        with open(path, encoding="utf-8") as f:
            text = json.dumps(json.load(f), ensure_ascii=False)
        for key, label in [("300-400", "300～400万円"), ("400-500", "400～500万円"), ("500-600", "500～600万円")]:
            self.assertIn(f'"key": "{key}", "value": "{label}"', text)
        for wrong in migration.WRONG_TO_RIGHT:
            self.assertNotIn(f'"key": "{wrong}"', text)

    def make_row(self, demographic, income, n):
        user = User.objects.create_user(f"r{n}")
        family = InstrumentFamily.objects.create(name=f"fam{n}", chargeable=False)
        instrument = Instrument.objects.create(
            name=f"inst{n}", language="Japanese", form=f"Test{n}", min_age=8, max_age=36, family=family
        )
        study = Study.objects.create(
            researcher=user, name=f"s{n}", instrument=instrument, demographic=demographic
        )
        admin = Administration.objects.create(
            study=study, subject_id=1, repeat_num=1, url_hash=str(n) * 64,
            completed=True, due_date=timezone.now(),
        )
        return BackgroundInfo.objects.create(administration=admin, age=20, annual_income=income)

    def test_migration_remaps_only_japanese_form_rows(self):
        japanese = Demographic.objects.create(
            name="Japanese_no_NIH.json", path="/form_data/background_info/Japanese_no_NIH.json"
        )
        english = Demographic.objects.create(
            name="English.json", path="/form_data/background_info/English.json"
        )
        ja_rows = [self.make_row(japanese, k, i) for i, k in enumerate(["300-450", "50000-75000", "75000-100000", "600-700"], 1)]
        us_row = self.make_row(english, "50000-75000", 5)
        no_form_row = self.make_row(None, "75000-100000", 6)

        migration.forwards(apps, None)
        got = [BackgroundInfo.objects.get(pk=r.pk).annual_income for r in ja_rows]
        self.assertEqual(got, ["300-400", "400-500", "500-600", "600-700"])
        self.assertEqual(BackgroundInfo.objects.get(pk=us_row.pk).annual_income, "50000-75000")
        self.assertEqual(BackgroundInfo.objects.get(pk=no_form_row.pk).annual_income, "75000-100000")

        migration.backwards(apps, None)
        got = [BackgroundInfo.objects.get(pk=r.pk).annual_income for r in ja_rows]
        self.assertEqual(got, ["300-450", "50000-75000", "75000-100000", "600-700"])
