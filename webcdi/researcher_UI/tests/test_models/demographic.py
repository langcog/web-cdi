from django.test import TestCase, tag

from researcher_UI.models import Demographic

# models test


@tag("model")
class DemographicModelTest(TestCase):
    def setUp(self) -> None:

        self.demographic = Demographic.objects.create(
            name="Demographic Model Test", path="path/to/demographic/files/"
        )

    def test_demographic_creation(self):
        instance = self.demographic

        self.assertTrue(isinstance(instance, Demographic))
        self.assertEqual(instance.__str__(), f"{instance.name}")
