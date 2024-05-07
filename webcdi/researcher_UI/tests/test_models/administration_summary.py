from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from cdi_forms.models import BackgroundInfo
from researcher_UI.models import (Administration, AdministrationSummary,
                                  Instrument, InstrumentFamily, Study)
from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model")
class AdministrationSummaryModelTest(TestCase):

    def setUp(self) -> None:

        user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        instrument_family = InstrumentFamily.objects.create(
            name="Instrument Family Test Model", chargeable=False
        )

        instrument = Instrument.objects.create(
            name="Test Instrument",
            language="Test Language",
            form="Test Form",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )

        study = Study.objects.create(
            researcher=user,
            name="Test Study Instance",
            instrument=instrument,
            redirect_url="https://redirect_url.com/redirect/{source_id}",
        )

        self.administration = AdministrationSummary.objects.create(
            study=study,
            subject_id=1,
            repeat_num=1,
            url_hash="0123456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now(),
        )

        BackgroundInfo.objects.create(
            administration=self.administration, age=12, source_id="123456"
        )

        cat_instrument = Instrument.objects.create(
            name="CAT Test Instrument",
            language="Test Language",
            form="CAT",
            min_age=3,
            max_age=15,
            family=instrument_family,
        )
        cat_study = Study.objects.create(
            researcher=user,
            name="CAT Test Study Instance",
            instrument=cat_instrument,
            append_source_id_to_redirect=True,
            source_id_url_parameter_key="param_key",
            redirect_url="https://redirect_url.com/redirect/",
        )

        self.cat_administration = Administration.objects.create(
            study=cat_study,
            subject_id=1,
            repeat_num=1,
            url_hash="cat3456789012345678901234567890123456789012345678901234567890123",
            completed=False,
            due_date=timezone.now(),
        )

        BackgroundInfo.objects.create(
            administration=self.cat_administration, age=12, source_id="cat123456"
        )
        return super().setUp()

    @tag("admin")
    def test_admin(self):
        self.user = User.objects.create_superuser(
            "super-user", "content_tester@goldenstandard.com", "password"
        )

        self.client.login(username="super-user", password="password")

        # create test data
        instance = self.administration

        # run test

        url = reverse(
            "admin:researcher_UI_administrationsummary_change",
            args=(instance.pk,),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse(
            "admin:researcher_UI_administrationsummary_changelist",
        )
        response = self.client.get(get_admin_changelist_view_url(instance))
        self.assertEqual(response.status_code, 200)
