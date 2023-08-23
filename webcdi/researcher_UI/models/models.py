# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from .instrument_model import Instrument
from .researcher_model import Researcher
from .administration_model import Administration

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



# Model for stored gift card codes
class payment_code(models.Model):
    study = models.ForeignKey(
        "study", on_delete=models.CASCADE
    )  # Associated study name
    hash_id = models.CharField(
        max_length=128, unique=True, null=True
    )  # Populated with hash ID of participant that code was given to. Null until code is rewarded. Uniqueness is enforced (one administration can only have 1 code)
    added_date = models.DateTimeField(
        verbose_name="Date code was added to database", auto_now_add=True
    )  # Date that payment code was first added to database
    assignment_date = models.DateTimeField(
        verbose_name="Date code was given to participant", null=True
    )  # Date that payment code was given to a participant
    payment_type = models.CharField(
        max_length=50
    )  # Type of gift card code. Currently only 'Amazon' is allowed
    gift_amount = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="Monetary value"
    )  # Monetary amount associated with gift card code
    gift_code = models.CharField(max_length=50)  # Gift card code

    class Meta:
        unique_together = (
            "payment_type",
            "gift_code",
        )  # Each object must have a unique combination of code type and the actual gift card code itself


# Model for stored IP addresses (only stored for studies created by 'langcoglab' and specific studies marked to log IP addresses, under Stanford's IRB approval)
class ip_address(models.Model):
    study = models.ForeignKey(
        "study", on_delete=models.CASCADE
    )  # Study associated with IP address
    ip_address = models.CharField(max_length=30)  # Actual IP address
    date_added = models.DateTimeField(
        verbose_name="Date IP address was added to database", auto_now_add=True
    )  # Date that IP address was added to database.


KIND_OPTIONS = (("count", "count"), ("list", "list"))


class InstrumentScore(models.Model):
    """
    Class to store the instrument scoring mechanisms loaded from json files held in
    /cdi_forms/form_data/scoring/
    """

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    title = models.CharField(max_length=101)
    category = models.CharField(max_length=101)
    scoring_measures = models.CharField(max_length=101)
    order = models.IntegerField(default=999)
    kind = models.CharField(max_length=5, default="count", choices=KIND_OPTIONS)

    def __unicode__(self):
        return "%s: %s" % (self.instrument, self.title)

    def __str__(self):
        return f"%s: %s" % (self.instrument, self.title)

    class Meta:
        ordering = ["instrument", "order"]


class Measure(models.Model):
    """
    Class to store the measures and their values used for scoring
    """

    instrument_score = models.ForeignKey(InstrumentScore, on_delete=models.CASCADE)
    key = models.CharField(max_length=51)
    value = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.instrument_score} {self.key}"


class SummaryData(models.Model):
    """
    Class to store the administrations summary scores for the instrument scoring mechanisms loaded from json files held in
    /cdi_forms/form_data/scoring/
    """

    administration = models.ForeignKey(Administration, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"%s: %s" % (self.administration, self.title)

    class Meta:
        unique_together = ("administration", "title")
        ordering = ["administration"]


