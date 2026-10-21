from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, tag
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

    def test_csrf_failure_shows_friendly_page(self):
        # e.g. a login page left open too long, or cookies blocked
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("login"),
            {"username": "auth_tester", "password": "a-strong-password"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "This page expired", status_code=403)
        self.assertNotContains(response, "CSRF verification failed", status_code=403)


@tag("auth")
class LoginWithEmailTest(TestCase):
    """#722 part 1: log in with username or email (case-insensitive); an
    email shared by several accounts asks for the username; registration
    refuses an email that is already in use."""

    password = "a-strong-password"

    def setUp(self):
        self.user = User.objects.create_user(
            username="Email_Tester", password=self.password, email="Tester@Example.com"
        )

    def login(self, username, password=None):
        return self.client.post(
            reverse("login"),
            {"username": username, "password": password or self.password},
        )

    def assert_logged_in_as(self, response, user):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.wsgi_request.user, user)

    def assert_not_logged_in(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_with_username(self):
        self.assert_logged_in_as(self.login("Email_Tester"), self.user)

    def test_login_with_username_any_case(self):
        self.assert_logged_in_as(self.login("email_tester"), self.user)

    def test_login_with_email_any_case(self):
        self.assert_logged_in_as(self.login("tester@example.com"), self.user)
        self.client.logout()
        self.assert_logged_in_as(self.login("TESTER@EXAMPLE.COM"), self.user)

    def test_login_with_email_wrong_password(self):
        response = self.login("tester@example.com", password="wrong")
        self.assert_not_logged_in(response)
        self.assertContains(response, "Please enter a correct username and password.")

    def test_login_with_email_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        self.assert_not_logged_in(self.login("tester@example.com"))

    def test_exact_username_wins_over_other_case(self):
        other = User.objects.create_user(username="email_tester", password="other-password")
        self.assert_logged_in_as(self.login("email_tester", "other-password"), other)
        self.client.logout()
        self.assert_logged_in_as(self.login("Email_Tester"), self.user)
        self.client.logout()
        # neither exact: ambiguous, so no login
        self.assert_not_logged_in(self.login("EMAIL_TESTER"))

    def test_username_that_looks_like_an_email(self):
        user = User.objects.create_user(
            username="someone@example.org", password="other-password", email="x@example.net"
        )
        self.assert_logged_in_as(self.login("someone@example.org", "other-password"), user)

    def test_shared_email_asks_for_username(self):
        second = User.objects.create_user(
            username="second_account", password=self.password, email="tester@example.COM"
        )
        response = self.login("tester@example.com")
        self.assert_not_logged_in(response)
        self.assertContains(
            response,
            "More than one account uses this email address. Please log in with your username.",
        )
        # the usernames still work
        self.assert_logged_in_as(self.login("second_account"), second)
        self.client.logout()
        self.assert_logged_in_as(self.login("Email_Tester"), self.user)

    def test_login_form_label(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Username or email")

    def registration_payload(self, **overrides):
        payload = {
            "username": "new_researcher",
            "first_name": "New",
            "last_name": "Researcher",
            "email": "new@example.com",
            "institution": "Test Institution",
            "position": "Test Position",
            "password1": "an-even-stronger-password",
            "password2": "an-even-stronger-password",
        }
        payload.update(overrides)
        return payload

    def test_registration_rejects_used_email_any_case(self):
        response = self.client.post(
            reverse("django_registration_register"),
            self.registration_payload(email="TESTER@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email address already exists.")
        self.assertFalse(User.objects.filter(username="new_researcher").exists())
        self.assertEqual(User.objects.filter(email__iexact="tester@example.com").count(), 1)

    def test_registration_accepts_new_email(self):
        response = self.client.post(
            reverse("django_registration_register"), self.registration_payload()
        )
        self.assertRedirects(
            response, "/accounts/register/complete/", target_status_code=200
        )
        self.assertTrue(User.objects.filter(username="new_researcher").exists())
