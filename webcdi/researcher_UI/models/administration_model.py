from django.db import models

from django.shortcuts import reverse

class AdministrationManager(models.Manager):
    def is_active(self):
        return super().get_queryset().filter(is_active=True)

# Model for individual administrations
class Administration(models.Model):
    study = models.ForeignKey("study", on_delete=models.CASCADE)  # Study name
    subject_id = models.IntegerField()  # Subject ID, unique to the associated study
    local_lab_id = models.CharField(
        max_length=101, blank=True, null=True
    )  # Id for local labs to use as they see fit
    repeat_num = models.IntegerField(
        verbose_name="Administration number"
    )  # Ordinal number of tests given to this particular subject ID. For example, if this is Subject 30's third test, this field will have '3' stored
    url_hash = models.CharField(max_length=128, unique=True)  # Associated URL hash
    scored = models.BooleanField(default=False)
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
    is_active = models.BooleanField(default=True)

    objects = AdministrationManager()

    class Meta:
        unique_together = (
            "study",
            "subject_id",
            "repeat_num",
        )  # Each administration object has a unique combination of study ID, subject ID, and administration number. They also have a unique hash ID identifier but uniqueness of hash ID is not enforced due to odds of 2 participants having the same hash ID being cosmically low.

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


class AdministrationSummary(Administration):
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


    def __str__(self):
        return f"%s %s" % (self.administration, self.item_ID)

