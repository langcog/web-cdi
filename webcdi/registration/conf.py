# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Confiurations of django-inspectional-registration
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from django.conf import settings
from appconf import AppConf


class InspectionalRegistrationAppConf(AppConf):
    DEFAULT_PASSWORD_LENGTH = 10
    BACKEND_CLASS = 'registration.backends.default.DefaultRegistrationBackend'
    SUPPLEMENT_CLASS = None
    SUPPLEMENT_ADMIN_INLINE_BASE_CLASS = (
        'registration.admin.RegistrationSupplementAdminInlineBase')
    OPEN = True

    #REGISTRATION_EMAIL = True
    ACCEPTANCE_EMAIL = True
    REJECTION_EMAIL = True
    ACTIVATION_EMAIL = True

    DJANGO_AUTH_URLS_ENABLE = True
    DJANGO_AUTH_URL_NAMES_PREFIX = ''
    DJANGO_AUTH_URL_NAMES_SUFFIX = ''

    # Issue #36
    USE_OBJECT_PERMISSION = False

    class Meta:
        prefix = 'registration'


def configure_other_settings():
    import warnings
    if not hasattr(settings, 'ACCOUNT_ACTIVATION_DAYS'):
        warnings.warn("You should set 'ACCOUNT_ACTIVATION_DAYS' in settings "
                      "module.")
        setattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 7)
    if not hasattr(settings,
            '_REGISTRATION_ADMIN_REQ_ATTR_NAME_IN_MODEL_INS'):
        setattr(settings,
                '_REGISTRATION_ADMIN_REQ_ATTR_NAME_IN_MODEL_INS',
                '_registration_admin_request')
    if not hasattr(settings, 'REGISTRATION_REGISTRATION_EMAIL'):
        setattr(settings,
                'REGISTRATION_REGISTRATION_EMAIL', True)
configure_other_settings()
