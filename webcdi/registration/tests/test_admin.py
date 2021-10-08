# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from django.test import TestCase
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.core import mail
from django.core import urlresolvers
from registration.compat import get_user_model
from registration.backends.default import DefaultRegistrationBackend
from registration.models import RegistrationProfile
from registration.admin import RegistrationAdmin
from registration.tests.mock import mock_request
from registration.tests.compat import override_settings


@override_settings(
    ACCOUNT_ACTIVATION_DAYS=7,
    REGISTRATION_OPEN=True,
    REGISTRATION_SUPPLEMENT_CLASS=None,
    REGISTRATION_BACKEND_CLASS=(
        'registration.backends.default.DefaultRegistrationBackend'),
)
class RegistrationAdminTestCase(TestCase):

    def setUp(self):
        User = get_user_model()
        self.backend = DefaultRegistrationBackend()
        self.mock_request = mock_request()
        self.admin = User.objects.create_superuser(
            username='mark', email='mark@test.com',
            password='password')

        self.client.login(username='mark', password='password')
        self.admin_url = reverse('admin:index')

    def test_change_list_view_get(self):
        url = urlresolvers.reverse('admin:registration_registrationprofile_changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'admin/change_list.html')

    def test_change_view_get(self):
        self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'admin/registration/registrationprofile/change_form.html'
        )

    def test_change_view_get_404(self):
        self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(100,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_change_view_post_valid_accept_from_untreated(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        redirect_url = urlresolvers.reverse('admin:registration_registrationprofile_changelist')
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'accept'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'accepted')

    def test_change_view_post_valid_accept_from_accepted(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)
        self.backend.accept(
            new_user.registration_profile,
            request=self.mock_request)
        previous_activation_key = new_user.registration_profile.activation_key
        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        redirect_url = urlresolvers.reverse('admin:registration_registrationprofile_changelist')
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'accept'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'accepted')
        self.assertNotEqual(profile.activation_key, previous_activation_key)

    def test_change_view_post_valid_accept_from_rejected(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)
        self.backend.reject(
            new_user.registration_profile,
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        redirect_url = urlresolvers.reverse('admin:registration_registrationprofile_changelist')
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'accept'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'accepted')

    def test_change_view_post_valid_reject_from_untreated(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        redirect_url = urlresolvers.reverse('admin:registration_registrationprofile_changelist')
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'reject'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'rejected')

    def test_change_view_post_invalid_reject_from_accepted(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)
        self.backend.accept(
            new_user.registration_profile,
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'reject'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'admin/registration/registrationprofile/change_form.html'
        )
        self.failIf(response.context['adminform'].form.is_valid())
        self.assertEqual(
            response.context['adminform'].form.errors['action_name'],
            ["Select a valid choice. "
             "reject is not one of the available choices."])

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'accepted')

    def test_change_view_post_invalid_reject_from_rejected(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)
        self.backend.reject(
            new_user.registration_profile,
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'reject'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'admin/registration/registrationprofile/change_form.html'
        )
        self.failIf(response.context['adminform'].form.is_valid())
        self.assertEqual(
            response.context['adminform'].form.errors['action_name'],
            ["Select a valid choice. "
             "reject is not one of the available choices."])

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'rejected')

    def test_change_view_post_invalid_activate_from_untreated(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'activate'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'admin/registration/registrationprofile/change_form.html'
        )
        self.failIf(response.context['adminform'].form.is_valid())
        self.assertEqual(
            response.context['adminform'].form.errors['action_name'],
            ["Select a valid choice. "
             "activate is not one of the available choices."])

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'untreated')

    def test_change_view_post_valid_activate_from_accepted(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)
        self.backend.accept(
            new_user.registration_profile,
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        redirect_url = urlresolvers.reverse('admin:registration_registrationprofile_changelist')
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'activate'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

        profile = RegistrationProfile.objects.filter(user__pk=new_user.pk)
        self.failIf(profile.exists())

    def test_change_view_post_invalid_activate_from_rejected(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)
        self.backend.reject(
            new_user.registration_profile,
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'activate'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'admin/registration/registrationprofile/change_form.html'
        )
        self.failIf(response.context['adminform'].form.is_valid())
        self.assertEqual(
            response.context['adminform'].form.errors['action_name'],
            ["Select a valid choice. "
             "activate is not one of the available choices."])

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'rejected')

    def test_change_view_post_valid_force_activate_from_untreated(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        redirect_url = urlresolvers.reverse('admin:registration_registrationprofile_changelist')
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'force_activate'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

        profile = RegistrationProfile.objects.filter(user__pk=new_user.pk)
        self.failIf(profile.exists())

    def test_change_view_post_invalid_force_activate_from_accepted(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)
        self.backend.accept(
            new_user.registration_profile,
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'force_activate'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'admin/registration/registrationprofile/change_form.html'
        )
        self.failIf(response.context['adminform'].form.is_valid())
        self.assertEqual(
            response.context['adminform'].form.errors['action_name'],
            ["Select a valid choice. "
             "force_activate is not one of the available choices."])

        profile = RegistrationProfile.objects.get(user__pk=new_user.pk)
        self.assertEqual(profile.status, 'accepted')

    def test_change_view_post_valid_force_activate_from_rejected(self):
        new_user = self.backend.register(
            username='bob', email='bob@example.com',
            request=self.mock_request)
        self.backend.reject(
            new_user.registration_profile,
            request=self.mock_request)

        url = urlresolvers.reverse('admin:registration_registrationprofile_change', args=(1,))
        redirect_url = urlresolvers.reverse('admin:registration_registrationprofile_changelist')
        response = self.client.post(url, {
            '_supplement-TOTAL_FORMS': 0,
            '_supplement-INITIAL_FORMS': 0,
            '_supplement-MAXNUM_FORMS': '',
            'action_name': 'force_activate'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

        profile = RegistrationProfile.objects.filter(user__pk=new_user.pk)
        self.failIf(profile.exists())

    def test_resend_acceptance_email_action(self):
        admin_class = RegistrationAdmin(RegistrationProfile, admin.site)

        self.backend.register(
            username='bob', email='bob@example.com', request=self.mock_request)
        admin_class.resend_acceptance_email(
            None, RegistrationProfile.objects.all())

        # one for registration, one for resend
        self.assertEqual(len(mail.outbox), 2)

    def test_accept_users_action(self):
        admin_class = RegistrationAdmin(RegistrationProfile, admin.site)

        self.backend.register(
            username='bob', email='bob@example.com', request=self.mock_request)
        admin_class.accept_users(None, RegistrationProfile.objects.all())

        for profile in RegistrationProfile.objects.all():
            self.assertEqual(profile.status, 'accepted')
            self.assertNotEqual(profile.activation_key, None)

    def test_reject_users_action(self):
        admin_class = RegistrationAdmin(RegistrationProfile, admin.site)

        self.backend.register(
            username='bob', email='bob@example.com', request=self.mock_request)
        admin_class.reject_users(None, RegistrationProfile.objects.all())

        for profile in RegistrationProfile.objects.all():
            self.assertEqual(profile.status, 'rejected')
            self.assertEqual(profile.activation_key, None)

    def test_force_activate_users_action(self):
        admin_class = RegistrationAdmin(RegistrationProfile, admin.site)

        self.backend.register(
            username='bob', email='bob@example.com', request=self.mock_request)
        admin_class.force_activate_users(
            None, RegistrationProfile.objects.all())

        self.assertEqual(RegistrationProfile.objects.count(), 0)

    @override_settings(REGISTRATION_SUPPLEMENT_CLASS=None)
    def test_get_inline_instances_without_supplements(self):
        admin_class = RegistrationAdmin(RegistrationProfile, admin.site)
        # Prevent caching
        if hasattr(admin_class.backend, '_supplement_class_cache'):
            delattr(admin_class.backend, '_supplement_class_cache')

        inline_instances = admin_class.get_inline_instances(self.mock_request, None)
        self.assertEqual(len(inline_instances), 0)

    @override_settings(
        REGISTRATION_SUPPLEMENT_CLASS="registration.supplements.default.models.DefaultRegistrationSupplement"
    )
    def test_get_inline_instances_with_default_supplements(self):
        admin_class = RegistrationAdmin(RegistrationProfile, admin.site)
        # Prevent caching
        if hasattr(admin_class.backend, '_supplement_class_cache'):
            delattr(admin_class.backend, '_supplement_class_cache')

        inline_instances = admin_class.get_inline_instances(self.mock_request, None)
        self.assertEqual(len(inline_instances), 1)
