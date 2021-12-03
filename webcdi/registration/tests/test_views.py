# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
import datetime
from django.test import TestCase
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse

from registration.compat import get_user_model
from registration import forms
from registration.models import RegistrationProfile
from registration.backends.default import DefaultRegistrationBackend

from registration.tests.compat import override_settings
from registration.tests.mock import mock_request


@override_settings(
        ACCOUNT_ACTIVATION_DAYS=7,
        REGISTRATION_OPEN=True,
        REGISTRATION_SUPPLEMENT_CLASS=None,
        REGISTRATION_BACKEND_CLASS=(
            'registration.backends.default.DefaultRegistrationBackend'),
    )
class RegistrationViewTestCase(TestCase):

    def setUp(self):
        self.backend = DefaultRegistrationBackend()
        self.mock_request = mock_request()


    def test_registration_view_get(self):
        """
        A ``GET`` to the ``register`` view uses the appropriate
        template and populates the registration form into the context.

        """
        response = self.client.get(reverse('registration_register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'registration/registration_form.html')
        self.failUnless(isinstance(response.context['form'],
                                   forms.RegistrationForm))

    def test_registration_view_post_success(self):
        """
        A ``POST`` to the ``register`` view with valid data properly
        creates a new user and issues a redirect.

        """
        response = self.client.post(reverse('registration_register'),
                                    data={'username': 'alice',
                                          'email1': 'alice@example.com',
                                          'email2': 'alice@example.com'})
        self.assertRedirects(response,
                             'http://testserver%s' % reverse('registration_complete'))
        self.assertEqual(RegistrationProfile.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_registration_view_post_failure(self):
        """
        A ``POST`` to the ``register`` view with invalid data does not
        create a user, and displays appropriate error messages.

        """
        response = self.client.post(reverse('registration_register'),
                                    data={'username': 'bob',
                                          'email1': 'bobe@example.com',
                                          'email2': 'mark@example.com'})
        self.assertEqual(response.status_code, 200)
        self.failIf(response.context['form'].is_valid())
        self.assertFormError(response, 'form', field=None,
                             errors="The two email fields didn't match.")
        self.assertEqual(len(mail.outbox), 0)

    def test_registration_complete_view_get(self):
        """
        A ``GET`` to the ``complete`` view uses the appropriate
        template and populates the registration form into the context.

        """
        # register save registration_profile in the session
        response = self.client.post(reverse('registration_register'),
                                    data={'username': 'alice',
                                          'email1': 'alice@example.com',
                                          'email2': 'alice@example.com'})
        response = self.client.get(reverse('registration_complete'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'registration/registration_complete.html')
        self.failUnless(isinstance(response.context['registration_profile'],
                                   RegistrationProfile))
        profile = response.context['registration_profile']
        self.assertEqual(profile.user.username, 'alice')
        self.assertEqual(profile.user.email, 'alice@example.com')

    def test_registration_view_closed(self):
        """
        Any attempt to access the ``register`` view when registration
        is closed fails and redirects.

        """
        settings.REGISTRATION_OPEN = False

        closed_redirect = 'http://testserver%s' % reverse('registration_disallowed')

        response = self.client.get(reverse('registration_register'))
        self.assertRedirects(response, closed_redirect)

        # Even if valid data is posted, it still shouldn't work.
        response = self.client.post(reverse('registration_register'),
                                    data={'username': 'alice',
                                          'email1': 'alice@example.com',
                                          'email2': 'alice@example.com'})
        self.assertRedirects(response, closed_redirect)
        self.assertEqual(RegistrationProfile.objects.count(), 0)

        settings.REGISTRATION_OPEN = True

    def test_activation_view_get_success(self):
        """
        A ``GET`` to the ``ActivationView`` view with valid activation_key

        """
        new_user = self.backend.register(username='alice', email='alice@example.com', request=self.mock_request)
        new_user = self.backend.accept(new_user.registration_profile, request=self.mock_request)
    
        activation_url = reverse('registration_activate', kwargs={
            'activation_key': new_user.registration_profile.activation_key})

        response = self.client.get(activation_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'registration/activation_form.html')
        self.failUnless(isinstance(response.context['form'],
                                   forms.ActivationForm))

    def test_activation_view_get_fail(self):
        """
        A ``GET`` to the ``ActivationView`` view wht invalid activation_key 
        raise Http404

        """
        self.backend.register(username='alice', email='alice@example.com', request=self.mock_request)
    
        activation_url = reverse('registration_activate', kwargs={
            'activation_key': 'invalidactivationkey'})

        response = self.client.get(activation_url)
        self.assertEqual(response.status_code, 404)

    def test_activation_view_post_success(self):
        """
        A ``POST`` to the ``ActivationView`` view with valid data properly
        handles a valid activation

        """
        User = get_user_model()
        new_user = self.backend.register(username='alice', email='alice@example.com', request=self.mock_request)
        new_user = self.backend.accept(new_user.registration_profile, request=self.mock_request)
    
        activation_url = reverse('registration_activate', kwargs={
            'activation_key': new_user.registration_profile.activation_key})

        response = self.client.post(activation_url,{
            'password1': 'swordfish',
            'password2': 'swordfish'})

        success_redirect = 'http://testserver%s' % reverse('registration_activation_complete')
        self.assertRedirects(response, success_redirect)
        # RegistrationProfile should be removed with activation
        self.assertEqual(RegistrationProfile.objects.count(), 0)
        # registration, acceptance and activation
        self.assertEqual(len(mail.outbox), 3)
        self.failUnless(User.objects.get(username='alice').is_active)

    def test_activation_view_post_failure(self):
        """
        A ``POST`` to the ``ActivationView`` view with invalid data does not
        activate a user, and raise Http404

        """
        expired_user = self.backend.register(username='alice', email='alice@example.com', request=self.mock_request)
        expired_user = self.backend.accept(expired_user.registration_profile, request=self.mock_request)
        expired_user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS+1)
        expired_user.save()
    
        activation_url = reverse('registration_activate', kwargs={
            'activation_key': expired_user.registration_profile.activation_key})

        response = self.client.post(activation_url,{
            'password1': 'swordfish',
            'password2': 'swordfish'})

        self.assertEqual(response.status_code, 404)
