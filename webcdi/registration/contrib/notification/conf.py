# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
"""
__author__ = "Alisue <lambdalisue@hashnote.net>"
from appconf import AppConf
from django.conf import settings


class InspectionalRegistrationNotificationAppConf(AppConf):
    NOTIFICATION = True
    NOTIFICATION_ADMINS = True
    NOTIFICATION_MANAGERS = True
    NOTIFICATION_RECIPIENTS = None

    NOTIFICATION_EMAIL_TEMPLATE_NAME = r"registration/notification_email.txt"
    NOTIFICATION_EMAIL_SUBJECT_TEMPLATE_NAME = (
        r"registration/notification_email_subject.txt"
    )

    class Meta:
        prefix = "registration"
