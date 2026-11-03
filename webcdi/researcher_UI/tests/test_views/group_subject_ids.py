from django.contrib.auth.models import User
from django.utils import timezone

from researcher_UI.models import Administration, Demographic, Instrument, Study
from researcher_UI.utils import max_subject_id

from .new_parent_links import NewParentTestCase


class GroupSubjectIdTest(NewParentTestCase):
    """Subject IDs on a grouped study continue from the researcher's whole group."""

    def setUp(self):
        super().setUp()
        self.study = self.make_study(study_group="pair")
        self.other_in_group = self.make_study(name="Other in pair", study_group="pair")
        self.add_row(self.other_in_group, 7)

    def add_row(self, study, subject_id):
        Administration.objects.create(
            study=study,
            subject_id=subject_id,
            repeat_num=1,
            url_hash=f"{study.pk:0>16}{subject_id:0>16}",
            completed=False,
            due_date=timezone.now(),
        )

    def test_continues_from_the_researchers_group(self):
        self.assertEqual(max_subject_id(self.study), 7)

    def test_ignores_another_researchers_group_of_the_same_name(self):
        other_researcher = User.objects.create_user(
            username="other_owner_name", password="x-test-only"
        )
        elsewhere = Study.objects.create(
            researcher=other_researcher,
            name="Elsewhere",
            instrument=Instrument.objects.get(language="English", form="WS"),
            min_age=12,
            max_age=36,
            demographic=Demographic.objects.get(name="English_Split.json"),
            study_group="pair",
        )
        self.add_row(elsewhere, 50)
        self.assertEqual(max_subject_id(self.study), 7)

    def test_no_demographic_link_creates_the_next_id(self):
        study = self.make_study(
            name="No demographic in pair",
            study_group="pair",
            no_demographic_boolean=True,
        )
        response = self.client.get(
            self.new_parent_url(study, source_id="abc", age=15, sex="m")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Administration.objects.get(study=study).subject_id, 8)
