# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from .researcher_model import Researcher

class Demographic(models.Model):
    """
    Class to store the different Demographic Form (Background Info) that can be used by Studies
    """

    name = models.CharField(max_length=30)
    path = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Researcher.objects.create(user=instance)
    instance.researcher.save()


from django.contrib.auth.models import User

User._meta.get_field("email")._unique = True


def get_meta_header():  # Returns a list of variables for administration objects
    return [
        "study",
        "subject_id",
        "administration_number",
        "link",
        "completed",
        "completedBackgroundInfo",
        "expiration_date",
        "last_modified",
    ]


def get_background_header():  # Returns a list of variables for backgroundinfo objects
    return [
        "id",
        "age",
        "sex",
        "birth_order",
        "birth_weight_lb",
        "birth_weight_kg",
        "early_or_late",
        "due_date_diff",
        "mother_yob",
        "mother_education",
        "father_yob",
        "father_education",
        "annual_income",
        "child_hispanic_latino",
        "caregiver_info",
        "other_languages_boolean",
        "language_from",
        "language_days_per_week",
        "language_hours_per_day",
        "ear_infections_boolean",
        "ear_infections",
        "hearing_loss_boolean",
        "hearing_loss",
        "vision_problems_boolean",
        "vision_problems",
    ]


