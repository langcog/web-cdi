# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import redirect, reverse

from .instrument import instrument
from .researcher import researcher


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
        researcher.objects.create(user=instance)
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


# Model for individual administrations
class administration(models.Model):
    study = models.ForeignKey("study", on_delete=models.CASCADE)  # Study name
    subject_id = models.IntegerField()  # Subject ID, unique to the associated study
    local_lab_id = models.CharField(
        max_length=101, blank=True, null=True
    )  # Id for local labs to use as they see fit
    repeat_num = models.IntegerField(
        verbose_name="Administration number"
    )  # Ordinal number of tests given to this particular subject ID. For example, if this is Subject 30's third test, this field will have '3' stored
    url_hash = models.CharField(max_length=128, unique=True)  # Associated URL hash
    completed = (
        models.BooleanField()
    )  # Whether administration has been marked as completed
    completedBackgroundInfo = models.BooleanField(
        verbose_name="Completed Background Info (P1)", default=False
    )  # Whether backgroundinfo has been completed
    completedSurvey = models.BooleanField(
        verbose_name="Completed Survey", default=False
    )  # Because we're adding the functionality to add background info after completing the survey, this tells us if the survey has been completed - note, it is only used when background info collected after survey
    due_date = models.DateTimeField(
        verbose_name="Expiration date"
    )  # Expiration date for administration
    last_modified = models.DateTimeField(
        auto_now=True
    )  # Date when the administration object was last updated
    created_date = models.DateTimeField(
        verbose_name="Creation date", auto_now_add=True
    )  # Date administration object was created
    page_number = models.IntegerField(
        verbose_name="Page number", default=0
    )  # Current progress for CDI form
    analysis = models.BooleanField(
        verbose_name="Confirmed Age and Completion", default=None, null=True
    )  # Whether participant confirmed child's age and that form was completed to best of ability
    bypass = models.BooleanField(
        verbose_name="Willing to forgo payment", default=None, null=True
    )  # Whether participant explicitly bypassed overflow page if study has reached subject cap
    include = models.BooleanField(
        verbose_name="Include for eventual analysis", default=True, null=True
    )  # Field for marking if a researcher wants to include data in study. Currently not used.
    opt_out = models.BooleanField(
        verbose_name="Participant opted out of broader sharing", default=None, null=True
    )

    class Meta:
        unique_together = (
            "study",
            "subject_id",
            "repeat_num",
        )  # Each administration object has a unique combination of study ID, subject ID, and administration number. They also have a unique hash ID identifier but uniqueness of hash ID is not enforced due to odds of 2 participants having the same hash ID being cosmically low.

    def __unicode__(self):
        return "%s %s %s" % (self.study, self.subject_id, self.repeat_num)

    def __str__(self):
        return f"%s %s %s" % (self.study, self.subject_id, self.repeat_num)

    def get_meta_data(self):
        return [
            self.study,
            self.subject_id,
            self.repeat_num,
            self.url_hash,
            self.completed,
            self.completedBackgroundInfo,
            self.due_date,
            self.last_modified,
        ]

    def get_absolute_url(self):
        if self.study.instrument.form in ["CAT"]:
            return reverse(
                "cat_forms:administer_cat_form", kwargs={"hash_id": self.url_hash}
            )
        else:
            return reverse("administer_cdi_form", kwargs={"hash_id": self.url_hash})

    def redirect_url(self):
        target = f"{self.study.redirect_url}"
        if self.study.append_source_id_to_redirect:
            target = f"{target}?{self.study.source_id_url_parameter_key}={self.backgroundinfo.source_id}"
        return target
        if self.study.participant_source_boolean == 2:  # centiment
            return self.study.redirect_url + "&aid=" + self.backgroundinfo.source_id
        elif self.study.participant_source_boolean == 1:  # prolific
            return self.study.redirect_url


class AdministrationSummary(administration):
    class Meta:
        proxy = True
        verbose_name = "Administration Summary"
        verbose_name_plural = "Administration Summary"


# Model for item responses within an administration
class administration_data(models.Model):
    administration = models.ForeignKey(
        "administration", on_delete=models.CASCADE
    )  # Associated administration
    item_ID = models.CharField(max_length=101)  # ID associated for each CDI item
    value = models.CharField(
        max_length=600
    )  # Response given by participant to this particular item

    class Meta:
        unique_together = (
            "administration",
            "item_ID",
        )  # Each administation_data object must have a unique combination of administration ID and item ID.

    def __unicode__(self):
        return "%s %s" % (self.administration, self.item_ID)

    def __str__(self):
        return f"%s %s" % (self.administration, self.item_ID)


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

    instrument = models.ForeignKey(instrument, on_delete=models.CASCADE)
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

    administration = models.ForeignKey(administration, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"%s: %s" % (self.administration, self.title)

    class Meta:
        unique_together = ("administration", "title")
        ordering = ["administration"]


class Benchmark(models.Model):
    """
    Class to store benchmark data for each instrument and score.
    Data is loaded from csv files held in /cdi_forms/form_data/benchmarking/
    """

    instrument = models.ForeignKey(instrument, on_delete=models.CASCADE)
    instrument_score = models.ForeignKey(InstrumentScore, on_delete=models.CASCADE)
    percentile = models.IntegerField()
    age = models.IntegerField()
    raw_score = models.IntegerField()
    raw_score_boy = models.IntegerField()
    raw_score_girl = models.IntegerField()

    def __unicode__(self):
        return "%s : %s : %s" % (self.instrument_score, self.percentile, self.age)

    def __str__(self):
        return f"{self.instrument_score} {self.percentile} {self.age}"

    class Meta:
        ordering = ["instrument_score", "age", "percentile"]