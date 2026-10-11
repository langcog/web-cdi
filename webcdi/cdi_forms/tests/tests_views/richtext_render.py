from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from researcher_UI.models import Administration, Instrument, Study
from researcher_UI.tests import generate_fake_results

MARKDOWN_WITH_SCRIPT = "**Thank you** for [helping](https://x.org).<script>steal()</script>"


@tag("richtext")
class StudyRichTextRoundTripTest(TestCase):
    """End-to-end for the CKEditor -> Markdown change: a researcher-authored
    waiver / end message is stored verbatim (plain TextField, no editor
    mangling) and rendered to participants through the Markdown+bleach
    sanitizer — formatted, with the script stripped."""

    fixtures = [
        "researcher_UI/fixtures/researcher_UI_test_fixtures.json",
        "cdi_forms/fixtures/cdi_forms_test_fixtures.json",
    ]

    def setUp(self):
        self.user = User.objects.create_user(username="researcher", password="secret")
        instrument = Instrument.objects.get(language="English", form="WS")
        self.study = Study.objects.create(
            researcher=self.user,
            name="RichText Study",
            instrument=instrument,
            waiver=MARKDOWN_WITH_SCRIPT,
            end_message="bespoke",
            end_message_text=MARKDOWN_WITH_SCRIPT,
        )

    def test_field_stores_markdown_verbatim(self):
        # the field is a plain TextField now; nothing rewrites the content
        study = Study.objects.get(pk=self.study.pk)
        self.assertEqual(study.waiver, MARKDOWN_WITH_SCRIPT)
        self.assertEqual(study.end_message_text, MARKDOWN_WITH_SCRIPT)

    def test_end_message_renders_sanitized_to_participant(self):
        generate_fake_results(self.study, 1)
        administration = Administration.objects.filter(
            study=self.study, completed=True
        )[0]
        response = self.client.get(
            reverse(
                "administration_summary_view",
                kwargs={"hash_id": administration.url_hash},
            )
        )
        self.assertEqual(response.status_code, 200)
        # Markdown was rendered ...
        self.assertContains(response, "<strong>Thank you</strong>")
        self.assertContains(response, 'href="https://x.org"')
        # ... and the script was stripped
        self.assertNotContains(response, "<script>steal")
