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
from django.core.exceptions import ImproperlyConfigured
from registration.compat import get_user_model
from registration import forms
from registration import signals
from registration.backends import get_backend
from registration.backends.default import DefaultRegistrationBackend
from registration.models import RegistrationProfile
from registration.tests.utils import with_apps
from registration.tests.mock import mock_request
from registration.tests.compat import override_settings


class RegistrationBackendRetrievalTests(TestCase):

    def test_get_backend(self):
        backend = get_backend(
                'registration.backends.default.DefaultRegistrationBackend')
        self.failUnless(isinstance(backend, DefaultRegistrationBackend))

    def test_backend_error_invalid(self):
        self.assertRaises(ImproperlyConfigured, get_backend,
                'registration.backends.doesnotexist.NonExistenBackend')

    def test_backend_attribute_error(self):
        self.assertRaises(ImproperlyConfigured, get_backend,
                'registration.backends.default.NonexistenBackend')

@override_settings(
        ACCOUNT_ACTIVATION_DAYS=7,
        REGISTRATION_OPEN=True,
        REGISTRATION_SUPPLEMENT_CLASS=None,
        REGISTRATION_BACKEND_CLASS=(
            'registration.backends.default.DefaultRegistrationBackend'),
    )
class DefaultRegistrationBackendTestCase(TestCase):

    def setUp(self):
        self.backend = DefaultRegistrationBackend()
        self.mock_request = mock_request()


    def test_registration(self):
        new_user = self.backend.register(
                username='bob', email='bob@example.com',
                request=self.mock_request)

        self.assertEqual(new_user.username, 'bob')
        self.assertEqual(new_user.email, 'bob@example.com')

        self.failIf(new_user.is_active)
        self.failIf(new_user.has_usable_password())

        # A inspection profile was created, and an registration email
        # was sent.
        self.assertEqual(RegistrationProfile.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_acceptance(self):
        new_user = self.backend.register(
                username='bob', email='bob@example.com',
                request=self.mock_request)

        profile = new_user.registration_profile
        accepted_user = self.backend.accept(profile, request=self.mock_request)

        self.failUnless(accepted_user)
        self.assertEqual(profile, accepted_user.registration_profile)
        self.assertEqual(profile.status, 'accepted')
        self.assertNotEqual(profile.activation_key, None)

    def test_rejection(self):
        new_user = self.backend.register(
                username='bob', email='bob@example.com',
                request=self.mock_request)

        profile = new_user.registration_profile
        rejected_user = self.backend.reject(profile, request=self.mock_request)

        self.failUnless(rejected_user)
        self.assertEqual(profile, rejected_user.registration_profile)
        self.assertEqual(profile.status, 'rejected')
        self.assertEqual(profile.activation_key, None)

    def test_activation_with_password(self):
        new_user = self.backend.register(
                username='bob', email='bob@example.com',
                request=self.mock_request)

        profile = new_user.registration_profile
        self.backend.accept(profile, request=self.mock_request)
        activated_user = self.backend.activate(
                activation_key=profile.activation_key,
                request=self.mock_request,
                password='swardfish')

        self.failUnless(activated_user)
        self.assertEqual(activated_user, new_user)
        self.failUnless(activated_user.is_active)
        self.failUnless(activated_user.has_usable_password())
        self.failUnless(activated_user.check_password('swardfish'))

    def test_activation_without_password(self):
        new_user = self.backend.register(
                username='bob', email='bob@example.com',
                request=self.mock_request)

        profile = new_user.registration_profile
        self.backend.accept(profile, request=self.mock_request)
        activated_user = self.backend.activate(
                activation_key=profile.activation_key,
                request=self.mock_request)

        self.failUnless(activated_user)
        self.assertEqual(activated_user, new_user)
        self.failUnless(activated_user.is_active)
        self.failUnless(activated_user.has_usable_password())

    def test_untreated_activation(self):
        User = get_user_model()
        new_user = self.backend.register(
                username='bob', email='bob@example.com',
                request=self.mock_request)

        profile = new_user.registration_profile
        activated_user = self.backend.activate(
                activation_key=profile.activation_key,
                request=self.mock_request,
                password='swardfish')

        self.failIf(activated_user)
        new_user = User.objects.get(pk=new_user.pk)
        self.failIf(new_user.is_active)
        self.failIf(new_user.has_usable_password())

    def test_rejected_activation(self):
        User = get_user_model()
        new_user = self.backend.register(
                username='bob', email='bob@example.com',
                request=self.mock_request)

        profile = new_user.registration_profile
        self.backend.reject(profile, request=self.mock_request)
        activated_user = self.backend.activate(
                activation_key=profile.activation_key,
                request=self.mock_request,
                password='swardfish')

        self.failIf(activated_user)
        new_user = User.objects.get(pk=new_user.pk)
        self.failIf(new_user.is_active)
        self.failIf(new_user.has_usable_password())

    def test_expired_activation(self):
        User = get_user_model()
        expired_user = self.backend.register(
                username='bob', email='bob@example.com',
                request=self.mock_request)

        profile = expired_user.registration_profile
        self.backend.accept(profile, request=self.mock_request)

        expired_user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS+1)
        expired_user.save()

        activated_user = self.backend.activate(
                activation_key=profile.activation_key,
                request=self.mock_request,
                password='swardfish')

        self.failIf(activated_user)
        expired_user = User.objects.get(pk=expired_user.pk)
        self.failIf(expired_user.is_active)
        self.failIf(expired_user.has_usable_password())

    def test_allow(self):
        old_allowed = settings.REGISTRATION_OPEN
        settings.REGISTRATION_OPEN = True
        self.failUnless(self.backend.registration_allowed())

        settings.REGISTRATION_OPEN = False
        self.failIf(self.backend.registration_allowed())
        settings.REGISTRATION_OPEN = old_allowed

    def test_get_registration_form_class(self):
        form_class = self.backend.get_registration_form_class()
        self.failUnless(form_class is forms.RegistrationForm)

    def test_get_activation_form_class(self):
        form_class = self.backend.get_activation_form_class()
        self.failUnless(form_class is forms.ActivationForm)

    def test_get_registration_complete_url(self):
        User = get_user_model()
        fake_user = User()
        url = self.backend.get_registration_complete_url(fake_user)
        self.assertEqual(url, reverse('registration_complete'))

    def test_get_registration_closed_url(self):
        url = self.backend.get_registration_closed_url()
        self.assertEqual(url, reverse('registration_disallowed'))

    def test_get_activation_complete_url(self):
        User = get_user_model()
        fake_user = User()
        url = self.backend.get_activation_complete_url(fake_user)
        self.assertEqual(url, reverse('registration_activation_complete'))

    def test_registration_signal(self):
        def receiver(sender, user, profile, **kwargs):
            self.assertEqual(user.username, 'bob')
            self.assertEqual(user.registration_profile, profile)
            received_signals.append(kwargs.get('signal'))

        received_signals = []
        signals.user_registered.connect(receiver, sender=self.backend.__class__)

        self.backend.register(username='bob', email='bob@example.com', request=self.mock_request)

        self.assertEqual(len(received_signals), 1)
        self.assertEqual(received_signals, [signals.user_registered])

    @with_apps(
        'django.contrib.contenttypes',
        'registration.supplements.default'
    )
    @override_settings(
            REGISTRATION_SUPPLEMENT_CLASS=(
                'registration.supplements.default.models.DefaultRegistrationSupplement'),
        )
    def test_registration_signal_with_supplement(self):
        from registration.supplements.default.models import DefaultRegistrationSupplement
        supplement = DefaultRegistrationSupplement(remarks='foo')

        def receiver(sender, user, profile, **kwargs):
            self.assertEqual(user.username, 'bob')
            self.assertEqual(user.registration_profile, profile)
            self.assertEqual(user.registration_profile.supplement,
                             profile.supplement)
            self.assertEqual(profile.supplement.remarks, 'foo')
            received_signals.append(kwargs.get('signal'))

        received_signals = []
        signals.user_registered.connect(receiver, sender=self.backend.__class__)

        self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request,
            supplement=supplement,
        )

        self.assertEqual(len(received_signals), 1)
        self.assertEqual(received_signals, [signals.user_registered])


    def test_acceptance_signal(self):
        def receiver(sender, user, profile, **kwargs):
            self.assertEqual(user.username, 'bob')
            self.assertEqual(user.registration_profile, profile)
            received_signals.append(kwargs.get('signal'))

        received_signals = []
        signals.user_accepted.connect(receiver, sender=self.backend.__class__)

        self.backend.register(username='bob', email='bob@example.com', request=self.mock_request)
        profile = RegistrationProfile.objects.get(user__username='bob')
        self.backend.accept(profile, request=self.mock_request)

        self.assertEqual(len(received_signals), 1)
        self.assertEqual(received_signals, [signals.user_accepted])

    def test_acceptance_signal_fail(self):
        def receiver(sender, user, profile, **kwargs):
            self.assertEqual(user.username, 'bob')
            self.assertEqual(user.registration_profile, profile)
            received_signals.append(kwargs.get('signal'))

        received_signals = []

        self.backend.register(username='bob', email='bob@example.com', request=self.mock_request)
        profile = RegistrationProfile.objects.get(user__username='bob')
        self.backend.accept(profile, request=self.mock_request)

        signals.user_accepted.connect(receiver, sender=self.backend.__class__)
        # accept -> accept is not allowed thus fail
        self.backend.accept(profile, request=self.mock_request)

        self.assertEqual(len(received_signals), 0)

    def test_rejection_signal(self):
        def receiver(sender, user, profile, **kwargs):
            self.assertEqual(user.username, 'bob')
            self.assertEqual(user.registration_profile, profile)
            received_signals.append(kwargs.get('signal'))

        received_signals = []
        signals.user_rejected.connect(receiver, sender=self.backend.__class__)

        self.backend.register(username='bob', email='bob@example.com', request=self.mock_request)
        profile = RegistrationProfile.objects.get(user__username='bob')
        self.backend.reject(profile, request=self.mock_request)

        self.assertEqual(len(received_signals), 1)
        self.assertEqual(received_signals, [signals.user_rejected])

    def test_rejection_signal_fail(self):
        def receiver(sender, user, profile, **kwargs):
            self.assertEqual(user.username, 'bob')
            self.assertEqual(user.registration_profile, profile)
            received_signals.append(kwargs.get('signal'))

        received_signals = []
        signals.user_rejected.connect(receiver, sender=self.backend.__class__)

        self.backend.register(username='bob', email='bob@example.com', request=self.mock_request)
        profile = RegistrationProfile.objects.get(user__username='bob')
        self.backend.accept(profile, request=self.mock_request)
        # accept -> reject is not allowed
        self.backend.reject(profile, request=self.mock_request)

        self.assertEqual(len(received_signals), 0)

    def test_activation_signal(self):
        def receiver(sender, user, password, is_generated, **kwargs):
            self.assertEqual(user.username, 'bob')
            self.assertEqual(password, 'swordfish')
            self.failIf(is_generated)
            received_signals.append(kwargs.get('signal'))

        received_signals = []
        signals.user_activated.connect(receiver, sender=self.backend.__class__)

        self.backend.register(username='bob', email='bob@example.com', request=self.mock_request)
        profile = RegistrationProfile.objects.get(user__username='bob')
        self.backend.accept(profile, request=self.mock_request)
        self.backend.activate(profile.activation_key, request=self.mock_request, password='swordfish')

        self.assertEqual(len(received_signals), 1)
        self.assertEqual(received_signals, [signals.user_activated])

