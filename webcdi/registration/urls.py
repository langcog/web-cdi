# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
URLconf for django-inspectional-registration
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from registration.compat import url

from registration.views import RegistrationView
from registration.views import RegistrationClosedView
from registration.views import RegistrationCompleteView
from registration.views import ActivationView
from registration.views import ActivationCompleteView

urlpatterns = [
    url(r'^activate/complete/$', ActivationCompleteView.as_view(),
        name='registration_activation_complete'),
    url(r'^activate/(?P<activation_key>\w+)/$', ActivationView.as_view(),
        name='registration_activate'),
    url(r'^register/$', RegistrationView.as_view(),
        name='registration_register'),
    url(r'^register/closed/$', RegistrationClosedView.as_view(),
        name='registration_disallowed'),
    url(r'^register/complete/$', RegistrationCompleteView.as_view(),
        name='registration_complete'),
]

# django.contrib.auth
from registration.conf import settings
from django.contrib.auth import views as auth_views
if settings.REGISTRATION_DJANGO_AUTH_URLS_ENABLE:
    prefix = settings.REGISTRATION_DJANGO_AUTH_URL_NAMES_PREFIX
    suffix = settings.REGISTRATION_DJANGO_AUTH_URL_NAMES_SUFFIX

    import django
    if django.VERSION >= (1, 6):
        uidb = r"(?P<uidb64>[0-9A-Za-z_\-]+)"
        token = r"(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})"
        password_reset_confirm_rule = (
            r"^password/reset/confirm/%s/%s/$" % (uidb, token)
        )
    else:
        uidb = r"(?P<uidb36>[0-9A-Za-z]+)"
        token = r"(?P<token>.+)"
        password_reset_confirm_rule = (
            r"^password/reset/confirm/%s-%s/$" % (uidb, token)
        )

    urlpatterns += [
        url(r'^login/$', auth_views.LoginView.as_view(),
            {'template_name': 'registration/login.html'},
            name=prefix+'login'+suffix),
        url(r'^logout/$', auth_views.LogoutView.as_view(),
            {'template_name': 'registration/logout.html'},
            name=prefix+'logout'+suffix),
        url(r'^password/change/$', auth_views.PasswordChangeView.as_view(),
            name=prefix+'password_change'+suffix),
        url(r'^password/change/done/$', auth_views.PasswordChangeDoneView.as_view(),
            name=prefix+'password_change_done'+suffix),
        url(r'^password/reset/$', auth_views.PasswordResetView.as_view(),
            name=prefix+'password_reset'+suffix, kwargs=dict(
                post_reset_redirect=prefix+'password_reset_done'+suffix)),
        url(password_reset_confirm_rule,
            auth_views.PasswordResetConfirmView.as_view(),
            name=prefix+'password_reset_confirm'+suffix),
        url(r'^password/reset/complete/$', auth_views.PasswordResetCompleteView.as_view(),
            name=prefix+'password_reset_complete'+suffix),
        url(r'^password/reset/done/$', auth_views.PasswordResetDoneView.as_view(),
            name=prefix+'password_reset_done'+suffix),
    ]

import django
if django.VERSION <= (1, 8):
    from registration.compat import patterns
    urlpatterns = patterns('', *urlpatterns)
