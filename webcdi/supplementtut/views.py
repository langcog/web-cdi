# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# """
# Class based views for django-inspectional-registration
# """
# __author__ = 'Alisue <lambdalisue@hashnote.net>'
# from django.http import Http404
# from django.shortcuts import render, redirect
# from django.views.generic import TemplateView
# from django.views.generic.edit import ProcessFormView, FormMixin
# from django.views.generic.base import TemplateResponseMixin
# from django.views.generic.detail import SingleObjectMixin
# from django.utils.text import ugettext_lazy as _

# from registration.backends import get_backend
# from registration.models import RegistrationProfile

from registration.signals import user_registered, user_activated
from registration.models import RegistrationProfile
from researcher_UI.models import *
from django.contrib.auth import login, authenticate
from django.contrib.sites.models import Site

def save_researcher_profile_receiver(sender, user, profile, request, **kwargs):
    researcher_profile, created = researcher.objects.get_or_create(user = profile.user)
    profile.user.first_name = profile.supplement.first_name
    profile.user.last_name = profile.supplement.last_name
    researcher_profile.institution = profile.supplement.institution
    researcher_profile.position = profile.supplement.position
    
    profile.user.save()
    researcher_profile.save()

def activate_user_profile_receiver(sender, user, request, **kwargs):
    if not user.is_active:
    	user.is_active = True
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    user.save()
    login(request, user)

user_registered.connect(save_researcher_profile_receiver)
user_activated.connect(activate_user_profile_receiver)


