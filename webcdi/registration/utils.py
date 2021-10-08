# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Utilities for django-inspectional-registration
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
import random

from django.utils.encoding import force_text
#from django.utils.six.moves import range

from six.moves  import range

from registration.compat import sha1


def get_site(request):
    """get current ``django.contrib.Site`` instance

    return ``django.contrib.RequestSite`` instance when the ``Site`` is
    not installed.

    """
    try:
        from django.contrib.sites.shortcuts import get_current_site
    except ImportError:
        from django.contrib.sites.models import get_current_site
    return get_current_site(request)


def generate_activation_key(username):
    """generate activation key with username
    
    originally written by ubernostrum in django-registration_

    .. _django-registration: https://bitbucket.org/ubernostrum/django-registration
    """
    username = force_text(username)
    seed = force_text(random.random())
    salt = sha1(seed.encode('utf-8')).hexdigest()[:5]
    activation_key = sha1((salt+username).encode('utf-8')).hexdigest()
    return activation_key


def generate_random_password(length=10):
    """generate random password with passed length"""
    # Without 1, l, O, 0 because those character are hard to tell
    # the difference between in same fonts
    chars = '23456789abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
    password = "".join([random.choice(chars) for i in range(length)])
    return password


def send_mail(subject, message, from_email, recipients):
    """send mail to recipients
    
    this method use django-mailer_ ``send_mail`` method when
    the app is in ``INSTALLED_APPS``

    .. Note::
        django-mailer_ ``send_mail`` is not used duaring unittest
        because it is a little bit difficult to check the number of
        mail sent in unittest for both django-mailer and original
        django ``send_mail``

    .. _django-mailer: http://code.google.com/p/django-mailer/
    """
    from django.conf import settings
    from django.core.mail import send_mail as django_send_mail
    import sys
    if 'test' not in sys.argv and 'mailer' in settings.INSTALLED_APPS:
        try:
            from mailer import send_mail
            return send_mail(subject, message, from_email, recipients)
        except ImportError:
            pass
    return django_send_mail(subject, message, from_email, recipients)
