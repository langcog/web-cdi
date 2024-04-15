# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import login

from registration.signals import user_activated, user_registered
from researcher_UI.models import *


def save_researcher_profile_receiver(sender, user, profile, request, **kwargs):
    researcher_profile, created = researcher.objects.get_or_create(user=profile.user)
    profile.user.first_name = profile.supplement.first_name
    profile.user.last_name = profile.supplement.last_name
    researcher_profile.institution = profile.supplement.institution
    researcher_profile.position = profile.supplement.position

    profile.user.save()
    researcher_profile.save()


def activate_user_profile_receiver(sender, user, request, **kwargs):
    if not user.is_active:
        user.is_active = True

    user.backend = "django.contrib.auth.backends.ModelBackend"
    user.save()
    login(request, user)


user_registered.connect(save_researcher_profile_receiver)


user_activated.connect(activate_user_profile_receiver)
