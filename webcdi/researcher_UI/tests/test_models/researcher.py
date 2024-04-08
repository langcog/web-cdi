from typing import Any

from django.contrib.auth.models import User
from django.test import TestCase, tag

from researcher_UI.models import Researcher

# models test


@tag("model", "new")
class ResearcherModelTest(TestCase):

    def setUp(self, **kwargs: Any) -> Any:

        user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )

        self.researcher, created = Researcher.objects.get_or_create(
            user=user,
        )

        self.researcher.institution = "Test Institution"
        self.researcher.position = "Test Position"
        self.researcher.save()

    def test_researcher_creation(self):
        instance = self.researcher

        self.assertTrue(isinstance(instance, Researcher))
        self.assertEqual(
            instance.__str__(),
            f"{instance.user.first_name} {instance.user.last_name} ({instance.position}, {instance.institution})",
        )
