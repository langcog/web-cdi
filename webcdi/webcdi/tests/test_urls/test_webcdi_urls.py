from django.test import TestCase, tag
from django.urls import resolve, reverse

from webcdi.views import CustomLoginView, CustomRegistrationView, HomeView


@tag("url")
class TestWebCDIUrls(TestCase):
    def setUp(self):
        pass

    def test_webcdi_login_url(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

        resolver = resolve(reverse("login"))
        self.assertEqual(resolver.func.view_class, CustomLoginView)

    def test_webcdi_home_url(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        resolver = resolve(reverse("home"))
        self.assertEqual(resolver.func.view_class, HomeView)

    def test_webcdi_registration_url(self):
        response = self.client.get(reverse("django_registration_register"))
        self.assertEqual(response.status_code, 200)

        resolver = resolve(reverse("django_registration_register"))
        self.assertEqual(resolver.func.view_class, CustomRegistrationView)

    def test_webcdi_about_url(self):
        # About page added in the facelift; content markers guard the template
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About Web-CDI")
        self.assertContains(response, "Wordbank")

    def test_webcdi_documentation_url(self):
        response = self.client.get(reverse("documentation"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "documentation")

    def test_health_endpoint_ok(self):
        # EB load-balancer probe; must not 500 (it did before the fix)
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
