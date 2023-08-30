import datetime

from brookes.models import BrookesCode
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from researcher_UI import choices


# Model for individual studies
class Study(models.Model):
    researcher = models.ForeignKey(
        "auth.user", on_delete=models.CASCADE
    )  # Researcher's name
    name = models.CharField(max_length=51)  # Study name
    instrument = models.ForeignKey(
        "instrument", on_delete=models.CASCADE
    )  # Instrument associated with study
    # waiver = models.TextField(blank = True) # IRB Waiver of documentation for study or any additional instructions provided to participant
    waiver = RichTextUploadingField(verbose_name="Opening Dialog Box", blank=True)
    study_group = models.CharField(max_length=51, blank=True)  # Study group
    anon_collection = models.BooleanField(
        default=False
    )  # Whether participants in study will all be anonymous
    subject_cap = models.IntegerField(
        blank=True, null=True
    )  # Subject cap to limit number of completed administrations
    confirm_completion = models.BooleanField(
        default=False
    )  # Whether to have participant confirm child's age and that test was completed to best of ability at end of study
    allow_payment = models.BooleanField(
        default=False
    )  # Whether to reward participants with gift card codes upon completion
    allow_sharing = models.BooleanField(
        default=False
    )  # Whether to allow participants to share results via Facebook
    test_period = models.IntegerField(
        default=14, validators=[MinValueValidator(1), MaxValueValidator(1095)]
    )  # Number of days after test creation that a participant may work on and complete administration
    prefilled_data = models.IntegerField(default=0)
    min_age = models.IntegerField(
        verbose_name="Minimum age", blank=True, null=True
    )  # Minimum age in months for study
    max_age = models.IntegerField(
        verbose_name="Maximum age", blank=True, null=True
    )  # Maximum age in months for study
    birth_weight_units = models.CharField(max_length=5, default="lb")
    show_feedback = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    timing = models.IntegerField(default=6)
    confirmation_questions = models.BooleanField(
        default=False
    )  # Whether to ask participant to restate primary carer age and child weight
    redirect_boolean = models.BooleanField(
        verbose_name="Provide redirect button at completion of study?", default=False
    )  # Whether to give redirect button upon completion of administration

    participant_source_boolean = models.IntegerField(
        default=0, choices=choices.PARTICIPANT_SOURCE_CHOICES
    )  # Whether this is capturing a link from a Partner sourcing participants
    redirect_url = models.URLField(
        blank=True, null=True, help_text="Please enter redirect URL"
    )  # The redirect URL
    direct_redirect_boolean = models.BooleanField(
        default=True,
        help_text="Deselect this if the redirect url calls an API to get the actual redirect url"
    )
    json_redirect = models.JSONField(
        blank=True, null=True,
        help_text="Enter redirect json here"
    )
    append_source_id_to_redirect = models.BooleanField(
        verbose_name="Append source_id to redirect URL?", default=False
    )
    hide_source_id = models.BooleanField(
        verbose_name="Hide source id from parents/participants?", default=False
    )
    source_id_url_parameter_key = models.CharField(
        "URL parameter key", blank=True, null=True, max_length=51
    )

    backpage_boolean = models.BooleanField(
        default=True,
        help_text="When selected the final demographics page will be shown - deselect to not show the final page",
    )
    print_my_answers_boolean = models.BooleanField(
        default=True
    )  # Whether to show print my answers button to user

    end_message = models.CharField(
        max_length=10, choices=choices.END_MESSAGE_CHOICES, default="standard"
    )
    end_message_text = RichTextUploadingField(blank=True, null=True)

    no_demographic_boolean = models.BooleanField(
        default = False,
        help_text ='You must include DOB, age offset and sex in the Link URL'
    )
    demographic = models.ForeignKey(
        "Demographic", on_delete=models.SET_NULL, blank=True, null=True
    )
    share_opt_out = models.BooleanField(
        default=False,
        help_text="For chargeable instruments you may opt out of sharing the study data.",
    )
    demographic_opt_out = models.BooleanField(
        default=False,
        help_text="For chargeable instruments you may opt out of collecting demographic data.",
    )
    send_completion_flag_url = models.URLField(
        blank=True,
        null=True,
        help_text = 'Send completion flag to URL'
    )
    api_token = models.CharField(max_length=101, blank=True, null=True)
    completion_data = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Data to be included in the completion url."
    )

    def __str__(self):
        return self.name

    def valid_code(self, user):
        if (
            self.instrument.family.chargeable
            and not BrookesCode.objects.filter(
                researcher=user,
                instrument_family=self.instrument.family,
                expiry__gte=datetime.date.today(),
            ).exists()
        ):
            return False
        else:
            return True

    class Meta:
        unique_together = (
            "researcher",
            "name",
        )  # Each study in database must have a unique combination of researcher and name
