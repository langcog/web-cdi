# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
"""
__author__ = "Alisue <lambdalisue@hashnote.net>"
from appconf import AppConf
from django.conf import settings


class InspectionalRegistrationAutoLoginAppConf(AppConf):
    AUTO_LOGIN = True

    class Meta:
        prefix = "registration"
