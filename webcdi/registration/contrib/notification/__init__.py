# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Send notification emails to admins, managers or particular recipients 
when new user has registered in the site

admins or managers are determined from ``ADMINS`` and ``MANAGERS`` attribute of
``settings.py``

You can disable this notification feature by setting ``False`` to 
``REGISTRATION_NOTIFICATION``.
You can disable sending emails to admins by setting ``False`` to
``REGISTRATION_NOTIFICATION_ADMINS``.
You can disable sending emails to managers by settings ``False`` to
``REGISTRATION_NOTIFICATION_MANAGERS``.

If you need extra recipients for the notification email, set a list of email 
addresses or a function which return a list to 
``REGISTRATION_NOTIFICATION_RECIPIENTS``

The notification email use the following templates in default

``registration/notification_email.txt``
    Used for email body, the following context will be passed
    
    ``site``
        A instance of ``django.contrib.sites.models.Site`` or
        ``django.contrib.sites.models.RequestSite``

    ``user``
        A ``User`` instance who has just registered

    ``profile``
        A ``RegistrationProfile`` instance of the ``user``

``registration/notification_email_subject.txt``
    Used for email subject, the following context will be passed
    
    ``site``
        A instance of ``django.contrib.sites.models.Site`` or
        ``django.contrib.sites.models.RequestSite``

    ``user``
        A ``User`` instance who has just registered

    ``profile``
        A ``RegistrationProfile`` instance of the ``user``

    .. Note::
        Newlies of the template will be removed.

If you want to change the name of template, use following settings

-   ``REGISTRATION_NOTIFICATION_EMAIL_TEMPLATE_NAME``
-   ``REGISTRATION_NOTIFICATION_EMAIL_SUBJECT_TEMPLATE_NAME``

    
.. Note::
    This feature is not available in tests because default tests of 
    django-inspectional-registration are not assumed to test with contributes.

    If you do want this feature to be available in tests, set
    ``_REGISTRATION_NOTIFICATION_IN_TESTS`` to ``True`` in ``setUp()`` method
    of the test case class and delete the attribute in ``tearDown()`` method.

"""
__author__ = "Alisue <lambdalisue@hashnote.net>"
import sys

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string

from registration.utils import get_site
from registration.utils import send_mail
from registration.signals import user_registered
from registration.contrib.notification.conf import settings


def is_notification_enable():
    """get whether the registration notification is enable"""
    if not settings.REGISTRATION_NOTIFICATION:
        return False
    if 'test' in sys.argv and not getattr(settings,
                                          '_REGISTRATION_NOTIFICATION_IN_TESTS',
                                          False):
        # Registration Notification is not available in test to prevent the test
        # fails of ``registration.tests.*``.
        # For testing Registration Notification, you must set
        # ``_REGISTRATION_NOTIFICATION_IN_TESTS`` to ``True``
        return False
    admins = settings.REGISTRATION_NOTIFICATION_ADMINS
    managers = settings.REGISTRATION_NOTIFICATION_MANAGERS
    recipients = settings.REGISTRATION_NOTIFICATION_RECIPIENTS
    if not (admins or managers or recipients):
        # All REGISTRATION_NOTIFICATION_{ADMINS, MANAGERS, RECIPIENTS} = False
        # is same as REGISTRATION_NOTIFICATION = False but user should use
        # REGISTRATION_NOTIFICATION = False insted of setting False to all
        # settings of notification.
        import warnings
        warnings.warn(
            'To set ``registration.contrib.notification`` disable, '
            'set ``REGISTRATION_NOTIFICATION`` to ``False``')
        return False
    return True


def send_notification_email_reciver(sender, user, profile, request, **kwargs):
    """send a notification email to admins/managers"""
    if not is_notification_enable():
        return

    context = {
        'user': user,
        'profile': profile,
        'site': get_site(request),
    }
    subject = render_to_string(
        settings.REGISTRATION_NOTIFICATION_EMAIL_SUBJECT_TEMPLATE_NAME,
        context)
    subject = "".join(subject.splitlines())
    message = render_to_string(
        settings.REGISTRATION_NOTIFICATION_EMAIL_TEMPLATE_NAME,
        context)

    recipients = []
    if settings.REGISTRATION_NOTIFICATION_ADMINS:
        for userinfo in settings.ADMINS:
            recipients.append(userinfo[1])
    if settings.REGISTRATION_NOTIFICATION_MANAGERS:
        for userinfo in settings.MANAGERS:
            recipients.append(userinfo[1])
    if settings.REGISTRATION_NOTIFICATION_RECIPIENTS:
        method_or_iterable = settings.REGISTRATION_NOTIFICATION_RECIPIENTS
        if callable(method_or_iterable):
            recipients.extend(method_or_iterable())
        elif isinstance(method_or_iterable, (list, tuple)):
            recipients.extend(method_or_iterable)
        else:
            raise ImproperlyConfigured((
                '``REGISTRATION_NOTIFICATION_RECIPIENTS`` must '
                'be a list of recipients or function which return '
                'a list of recipients (Currently the value was "%s")'
            ) % method_or_iterable)
    # remove duplications
    recipients = frozenset(recipients)

    mail_from = getattr(settings, 'REGISTRATION_FROM_EMAIL', '') or \
                    settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
user_registered.connect(send_notification_email_reciver)
