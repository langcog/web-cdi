from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, tag
from django.urls import reverse


@tag("auth")
class AuthFlowsTest(TestCase):
    """Regression tests for the auth flows the Django 5 upgrade touched.

    Django 5.0 removed GET support from LogoutView, which silently broke
    every logout link in the app (found by QA, 2026-09). These lock in the
    POST-only behavior and the surrounding flows; none of this had coverage.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="auth_tester",
            password="a-strong-password",
            email="auth@example.com",
        )

    def test_login_post_authenticates(self):
        response = self.client.post(
            reverse("login"),
            {"username": "auth_tester", "password": "a-strong-password"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_post_bad_password_rerenders(self):
        response = self.client.post(
            reverse("login"), {"username": "auth_tester", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_get_returns_405(self):
        # Django 5 removed GET logout; a plain logout link must never come back
        self.client.force_login(self.user)
        response = self.client.get("/accounts/logout/")
        self.assertEqual(response.status_code, 405)

    def test_logout_post_logs_out(self):
        self.client.force_login(self.user)
        response = self.client.post("/accounts/logout/")
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        response = self.client.get(reverse("researcher_ui:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_navbar_logout_is_a_post_form(self):
        # the console navbar must render logout as a POST form, not a GET link
        self.client.force_login(self.user)
        content = self.client.get(reverse("researcher_ui:console")).content.decode()
        self.assertIn('action="/accounts/logout/"', content)
        self.assertNotIn('href="/accounts/logout/"', content)

    def test_admin_logout_post_only(self):
        admin = User.objects.create_superuser(
            "auth_admin", email="admin@example.com", password="a-strong-password"
        )
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("admin:logout")).status_code, 405)
        response = self.client.post(reverse("admin:logout"))
        # honors LOGOUT_REDIRECT_URL rather than rendering admin's logged_out page
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        response = self.client.get(reverse("researcher_ui:profile"))
        self.assertEqual(response.status_code, 302)

    def test_password_reset_sends_email(self):
        response = self.client.post(
            reverse("password_reset"), {"email": "auth@example.com"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("auth@example.com", mail.outbox[0].to)
