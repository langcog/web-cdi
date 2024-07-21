import logging

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from researcher_UI.views import Console

logger = logging.getLogger("selenium")
logger.setLevel(logging.INFO)


class ConsoleViewTest(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = User.objects.create_user(username="test_user", password="secret")

    def test_studies_set_in_context(self):
        request = RequestFactory().get(reverse("researcher_ui:console"))
        request.user = self.user
        view = Console()
        view.setup(request)
        context = view.get_context_data()
        self.assertIn("studies", context)
