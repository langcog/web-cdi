from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from registration.models import RegistrationProfile
# models test


@tag("model",)
class RegistrationProfileModelTest(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="PaulMcCartney", password="PaulMcCartney"
        )
        return super().setUp()
    
    @tag('model')
    def test_administration_creation(self):
        instance = RegistrationProfile(user=self.user)

        self.assertTrue(isinstance(instance, RegistrationProfile))
        self.assertEqual(
            instance.__str__(), f"Registration information for {instance.user}"
        )


    