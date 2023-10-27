from ckeditor_uploader.widgets import CKEditorUploadingWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Fieldset, Layout, Submit
from django import forms
from django.contrib.postgres.forms import IntegerRangeField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from form_utils.forms import BetterModelForm
from researcher_UI.models import *

from . import choices


# Form for creating a new study
class AddStudyForm(BetterModelForm):
    name = forms.CharField(label="Study Name", max_length=51)  # Study name
    instrument = forms.ModelChoiceField(
        queryset=Instrument.objects.filter(language="English"),
        empty_label="(choose from the list)",
    )  # Study instrument (CANNOT BE CHANGED LATER)
    no_demographic_boolean = forms.BooleanField(
        label="Minimum demographic data provided in URL link",
        help_text="You will need to include DOB, sex and age offset in the link URL.  For example http://127.0.0.1:8000/interface/henry/Henry%20Test%20-%20ws1/new_parent/?age={age}&offset={offset}&sex={sex}",
        required=False,
        # initial = False
    )
    demographic = forms.ModelChoiceField(
        queryset=Demographic.objects.all(), empty_label=_("Default"), required=False
    )  # demographic cannot be changed later
    waiver = forms.CharField(
        widget=CKEditorUploadingWidget(),
        label=_("Opening Dialog Box"),
        required=False,
    )  # Addition of an IRB waiver of documentation or any other instructive text can be added here
    allow_payment = forms.BooleanField(
        required=False,
        label='Would you like to pay subjects in the form of Amazon gift cards? (You will need to upload gift card codes under "Update Study").',
    )  # Whether study participants will be compensated in the form of gift card codes upon completion
    anon_collection = forms.BooleanField(
        required=False,
        label="Do you plan on collecting only anonymous data in this study? (e.g., posting ads on social media, mass emails, etc)",
    )  # Whether the study will have only anonymous participants (opens up a range of other settings for anonymous data collection)
    subject_cap = forms.IntegerField(
        label="Maximum number of participants",
        required=False,
        min_value=1,
        help_text="Leave this blank if you do NOT want to limit the number of participants.",
        widget=forms.NumberInput(attrs={"placeholder": "XXX participants"}),
    )  # If there are anonymous participants, you can set a cap that limits the number of tests that can be completed. Tests initiated before the cutoff can still be finished even after the cutoff is reached
    confirm_completion = forms.BooleanField(
        required=False,
        label="At the end of the form, would you like parents to confirm the age of their child and that they completed the entire test? (Best for anonymous data collections where you haven't personally vetted each participant)",
    )  # Asks participants to verify the child's age and that they completed the form to the best of their ability. Only for participants that have not been vetted.
    # allow_sharing = forms.BooleanField(required=False, label="Would you like participants to be able to share their Web-CDI results via Facebook?") # Gives option for participants to be able to share their results via Facebook. Default off.
    test_period = forms.IntegerField(
        label="# Days Before Expiration",
        help_text="Between 1 and 1095. Default is 14 days. (e.g., 14 = 14 days for parents to complete a form)",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "(e.g., 14 = 14 days to complete a form)",
                "min": "1",
                "max": "1095",
            }
        ),
    )  # Number of days that a participant can use to complete an administration before expiration. By default, participants have 14 days to complete test. Ranges from 1-28 days.
    age_range = IntegerRangeField(label="Age Range For Study (in months)")
    show_feedback = forms.BooleanField(
        required=False,
        initial=True,
        label="Would you like to show participants graphs of their data after completion?",
    )

    prefilled_data_choices = (
        (0, "No, do not populate the any part of the form"),
        (1, "Demographic Information Form"),
        # (2, "The Background Information Form and the Vocabulary Checklist"),
    )
    prefilled_data = forms.ChoiceField(
        choices=prefilled_data_choices,
        label="Pre-fill data for longitudinal participants?",
        help_text="For longitudinal participants, would you like to populate the test with responses from earlier tests?",
    )

    birth_weight_choices = (
        ("lb", "Measure birthweight in pounds and ounces"),
        ("kg", "Measure birthweight in kilograms"),
    )
    birth_weight_units = forms.ChoiceField(
        choices=birth_weight_choices, label="Measurement units for birthweight"
    )
    timing = forms.IntegerField(
        label="Minimum time (minutes) a parent must take to complete the study (default=6)",
        required=True,
        widget=forms.NumberInput(),
        initial=6,
    )

    confirmation_questions = forms.BooleanField(
        required=False,
        label="Would you like participants to answer the confirmation questions (only available when split demographic information forms are used)",
    )

    redirect_boolean = forms.BooleanField(
        label="Provide redirect button at completion of study?", required=False
    )  # Whether to give redirect button upon completion of administration
    redirect_url = forms.URLField(
        required=False,
        help_text="Enter the basic return URL including source_id within curly brackets {} if required",
        widget=forms.URLInput(
            attrs={"placeholder": "https://my_example.com/redirect_url/{source_id}/"}
        ),
    )
    direct_redirect_boolean = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Deselect this if the redirect url calls an API to get the actual redirect url",
    )
    JSON_REDIRECT_PLACEHOLDER = """
        {
            "token": "DD266E7616FE86C190DEBC530CE5E435"
            "content": "surveyLink"
            "format": "json"
            "instrument": "webcdi"
            "event": "v01_arm_1"
            "record": "YISKL0001"
            "returnFormat": "json"
        }
    """
    json_redirect = forms.JSONField(
        help_text="Enter redirect json here",
        required=False,
        widget=forms.Textarea(attrs={"placeholder": JSON_REDIRECT_PLACEHOLDER}),
    )

    participant_source_boolean = forms.ChoiceField(
        label="Participant Source", choices=choices.PARTICIPANT_SOURCE_CHOICES
    )  # Whether to give redirect button upon completion of administration
    append_source_id_to_redirect = forms.BooleanField(required=False)
    hide_source_id = forms.BooleanField(
        label="Hide source from participant/parent", required=False
    )
    source_id_url_parameter_key = forms.CharField(required=False)

    backpage_boolean = forms.BooleanField(
        label="Show backpage in split demographic information study?", required=False
    )

    print_my_answers_boolean = forms.BooleanField(
        label="Allow participant to print their responses at end of Study?",
        required=False,
    )

    end_message = forms.ChoiceField(choices=choices.END_MESSAGE_CHOICES)
    end_message_text = forms.CharField(widget=CKEditorUploadingWidget(), required=False)

    share_opt_out = forms.BooleanField(
        required=False,
        help_text="For chargeable instruments you may opt out of sharing the study data.",
    )
    demographic_opt_out = forms.BooleanField(
        label="Collect only Minimum demographic data (age, sex, age offset).",
        required=False,
        help_text="For chargeable instruments you may opt out of collecting demographic data.  We will still collect age, sex and whether born early or late for norming purposes.",
    )
    send_completion_flag_url = forms.URLField(
        required=False,
        help_text="Provide a URL to send a completion flag including source_id within curly brackets {} if required",
        widget=forms.URLInput(
            attrs={"placeholder": "https://my_example.com/completed/{source_id}/"}
        ),
    )

    completion_data = forms.JSONField(
        required=False,
        help_text="Provide JSON data to be included when sending the completion flag source_id and event_id within double curly brackets {{}} if required",
        widget=forms.Textarea(
            attrs={
                "placeholder": '[{"record_id": "{{source_id}}", "redcap_event_name": "{{event_id}}", "webcdi_completion_status": 1}]'
            }
        ),
    )
    gift_codes = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "Paste Amazon gift card codes here. Can be separated by spaces, commas, or new lines."
            }
        ),
        required=False,
        label="Gift Card Codes",
    )  # Can add a list of gift card codes (separated by new lines, commas, or spaces) to the PaymentCode model that are given out to participants upon completion of current study.
    gift_amount = forms.CharField(
        max_length=7,
        required=False,
        label="Amount per Card (in USD)",
        widget=forms.TextInput(attrs={"placeholder": "$XX.XX"}),
    )

    # Form validation. Form is passed automatically to views.py for higher level checking.
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    # Initiating form and field layout.
    def __init__(self, *args, **kwargs):
        self.researcher = kwargs.pop("researcher", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "add-study"
        self.helper.form_class = "form-horizontal"
        # self.helper.template = PROJECT_ROOT + '/../cdi_forms/templates/bootstrap3/whole_uni_form.html'
        # self.helper.template = 'bootstrap4/whole_uni_form.html'
        self.helper.label_class = "col-3"
        self.helper.field_class = "col-9"
        self.helper.form_method = "post"
        self.fields["backpage_boolean"].initial = True

        if self.researcher:
            self.fields["instrument"] = forms.ModelChoiceField(
                queryset=Instrument.objects.filter(
                    researcher=self.researcher.researcher
                ),
                empty_label="(choose from the list)",
            )
        else:
            try:
                self.fields["instrument"] = forms.ModelChoiceField(
                    queryset=Instrument.objects.filter(pk=self.instance.instrument.pk),
                    empty_label=None,
                )
            except:
                pass
            
            '''
            if self.instance.demographic:
                self.fields["demographic"] = forms.ModelChoiceField(
                    queryset=Demographic.objects.filter(
                        pk=self.instance.demographic.pk
                    ),
                    empty_label=None,
                )
            else:
                self.fields["demographic"] = forms.ModelChoiceField(
                    queryset=None, empty_label="Default"
                )
            '''

        # self.helper.form_action = reverse("researcher_ui:add_study")

        self.helper.layout = Layout(
            self.study_options_fieldset(),
            self.demographic_options_fieldset(),
            self.opening_dialog_fieldset(),
            self.redirect_options_fieldset(),
            self.completion_page_fieldset(),
            self.submit_fieldset(),
        )

    def study_options_fieldset(self):
        return Fieldset(
            "Study Options",
            Field("name"),
            Field("instrument"),
            Field("share_opt_out"),
            Field("test_period"),
            Field("birth_weight_units"),
            Field("timing"),
            Field("allow_payment", css_class="css_enabler"),
            Div(Field("gift_codes"), css_class="allow_payment collapse"),
            Div(Field("gift_amount"), css_class="allow_payment collapse"),
            Field("anon_collection"),
            Field("subject_cap"),
        )

    def demographic_options_fieldset(self):
        return Fieldset(
            "Demographic Options",
            Div(
                Field("demographic_opt_out"),
                Div(
                    Field("no_demographic_boolean", css_class="css_enabler"),
                    css_class="demographic_opt_out collapse",
                ),
                css_class="share_opt_out collapse",
            ),
            Div(
                Field("age_range"),
                Field("demographic", css_class="css_enabler"),
                Div(Field("backpage_boolean"), css_class="demographic"),
                Div(Field("confirmation_questions"), css_class="demographic"),
                Field("prefilled_data"),
                css_class="no_demographic_boolean collapse",
            ),
        )

    def opening_dialog_fieldset(self):
        return Fieldset(
            "Opening Dialog",
            Field("waiver"),
        )

    def redirect_options_fieldset(self):
        return Fieldset(
            "Redirect Options",
            HTML(
                """
                    <p>If you would like to connect web-cdi with an external service (e.g., prolific, mturk, lookit), please fill out the following options when applicable</p>
                """
            ),
            Field("redirect_boolean", css_class="css_enabler"),
            Div(
                Field("redirect_url"),
                Field("direct_redirect_boolean", css_class="css_enabler"),
                Div(
                    Field("json_redirect"), css_class="direct_redirect_boolean collapse"
                ),
                css_class="redirect_boolean collapse",
            ),
            Field("participant_source_boolean", css_class="css_enabler"),
            Div(
                Field("hide_source_id"),
                Field("send_completion_flag_url", css_class="css_enabler"),
                Div(
                    Field("completion_data"),
                    css_class="send_completion_flag_url collapse",
                ),
                css_class="participant_source_boolean collapse",
            ),
        )

    def completion_page_fieldset(self):
        return Fieldset(
            "Completion Page Details",
            Field("print_my_answers_boolean"),
            Field("confirm_completion"),
            Field("show_feedback"),
            Field("end_message", css_class="css_enabler"),
            Div(
                Field("end_message_text"),
                css_class="end_message collapse",
            ),
        )

    def submit_fieldset(self):
        return Submit("submit", _("Save"), css_class="btn btn-primary right")

    # Form is related to the study model. Exclude study group designation (is done post-creation) and researcher name (filled automatically)
    class Meta:
        model = Study
        exclude = ["study_group", "researcher"]


class EditStudyForm(AddStudyForm):
    def __init__(self, *args, **kwargs):
        self.researcher = kwargs.pop("researcher", None)
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            self.study_options_fieldset(),
            self.demographic_options_fieldset(),
            self.opening_dialog_fieldset(),
            self.redirect_options_fieldset(),
            self.completion_page_fieldset(),
            self.submit_fieldset(),
        )

    def clean(self):
        return super().clean()


# Form for grouping studies together
class AddPairedStudyForm(forms.ModelForm):
    study_group = forms.CharField(
        label="Study Group Name", max_length=51
    )  # Type out study group's name
    paired_studies = forms.ModelMultipleChoiceField(
        queryset=Study.objects.all()
    )  # List all studies created by researcher that are currently unpaired.

    class Meta:
        model = Study
        fields = (
            "study_group",
            "paired_studies",
        )

    # Form validation. The paired_studies field cannot be empty.
    def clean(self):
        cleaned_data = super(AddPairedStudyForm, self).clean()
        if not cleaned_data.get("paired_studies"):
            self.add_error("paired_studies", "Added studies cannot be blank")

    # Form initiation. Specify form and field layout. Updated paired_studies so that only unpaired studies associated with the researcher are displayed.
    def __init__(self, *args, **kwargs):
        self.researcher = kwargs.pop("researcher", None)
        super(AddPairedStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "add-paired-study"
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-3"
        self.helper.field_class = "col-9"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("researcher_ui:add_paired_study")
        if self.researcher:
            self.fields["paired_studies"] = forms.ModelMultipleChoiceField(
                queryset=Study.objects.filter(
                    study_group="", researcher=self.researcher
                )
            )


class ImportDataForm(forms.ModelForm):
    study = forms.ModelChoiceField(
        queryset=Study.objects.all(), empty_label="(choose from the list)"
    )
    imported_file = forms.FileField()

    class Meta:
        model = Study
        fields = ["study", "imported_file"]

    # Form validation. Form is passed automatically to views.py for higher level checking.
    def clean(self):
        cleaned_data = super(ImportDataForm, self).clean()
        if not cleaned_data.get("imported_file"):
            self.add_error("imported_file", "Please upload a file.")

    # Form initiation. Specify form and field layout. Updated paired_studies so that only unpaired studies associated with the researcher are displayed.
    def __init__(self, *args, **kwargs):
        self.researcher = kwargs.pop("researcher", None)
        self.study = kwargs.pop("study", None)
        super(ImportDataForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "import-data"
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-3"
        self.helper.field_class = "col-9"
        self.helper.form_method = "post"

        if self.researcher:
            self.fields["study"] = forms.ModelChoiceField(
                queryset=Study.objects.filter(researcher=self.researcher),
                empty_label="(choose from the list)",
            )
        if self.study:
            self.fields["study"].initial = self.study


class EditSubjectIDForm(forms.ModelForm):
    class Meta:
        model = Administration
        fields = ["subject_id", "study"]
        widgets = {"study": forms.HiddenInput()}

    def clean(self):
        cleaned_data = super(EditSubjectIDForm, self).clean()
        if Administration.objects.filter(
            study=cleaned_data["study"], subject_id=cleaned_data["subject_id"]
        ).exists():
            raise forms.ValidationError(
                "An Administration with this id already exists.  Select a unique value"
            )
        return cleaned_data


class EditLocalLabIDForm(forms.ModelForm):
    class Meta:
        model = Administration
        fields = ["local_lab_id", "study"]
        widgets = {"study": forms.HiddenInput()}


class EditOptOutForm(forms.ModelForm):
    class Meta:
        model = Administration
        fields = ["opt_out", "study"]
        widgets = {"study": forms.HiddenInput()}


class AddInstrumentForm(forms.ModelForm):
    class Meta:
        model = Researcher
        fields = ["allowed_instrument_families"]
        widgets = {"allowed_instrument_families": forms.CheckboxSelectMultiple()}


class AddChargeableInstrumentForm(forms.ModelForm):
    class Meta:
        model = Researcher
        fields = ["allowed_instrument_families"]
        widgets = {"allowed_instrument_families": forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["allowed_instrument_families"].queryset = self.fields[
            "allowed_instrument_families"
        ].queryset.filter(chargeable=True)


# Update study form
class StudyFormForm(forms.ModelForm):
    subject_id_old = forms.IntegerField()

    class Meta:
        model = Administration
        fields = [
            "id",
            "subject_id",
            "local_lab_id",
            "opt_out",
            "subject_id_old",
        ]


class AdminNewForm(forms.ModelForm):
    new_subject_ids = forms.CharField(required=False)
    autogenerate_count = forms.IntegerField(required=False)

    class Meta:
        model = Study
        fields = ("new_subject_ids", "autogenerate_count")
