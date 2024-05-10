from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from supplementtut.models import MyRegistrationSupplement

from researcher_UI.tests.utils import (get_admin_change_view_url,
                                       get_admin_changelist_view_url)

# models test


@tag("model")
class MyRegistrationSupplementModelTest(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_model_creation(self):
        first_name = 'First Name Test',
        last_name = 'Last Name Test',
        institution = 'Institution Test',
        position = 'Position Test',
        comments = 'Comments Test',
        instance = MyRegistrationSupplement(
            first_name = first_name,
            last_name = last_name,
            institution = institution,
            position = position,
            comments = comments,
        )

        self.assertTrue(isinstance(instance, MyRegistrationSupplement))
        self.assertEqual(
            instance.__str__(), f"{first_name} {last_name}, {position} ({institution})"
        )
