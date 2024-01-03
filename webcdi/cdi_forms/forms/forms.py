import datetime
import json
import os.path

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Fieldset, Layout, Submit
from django import forms
from django.conf import settings
from django.utils.translation import pgettext_lazy, gettext
from django.utils.translation import gettext_lazy as _
from form_utils.forms import BetterModelForm
from django.utils.html import mark_safe

from ..languages import LANGUAGE_OPTIONS as language_choices
from ..models import *
from ..utils import get_demographic_filename

PROJECT_ROOT = os.path.abspath(
    os.path.dirname(__file__)
)  # Declare project file directory

# isoLangs = json.load(codecs.open(PROJECT_ROOT + '/../' + 'languages.json', 'r', 'utf-8')) # Load up languages stored in languages.json in project root for other_languages question
# language_choices = [(v['name'],v['nativeName'] + " ("+ v['name'] + ")") for k,v in isoLangs.iteritems()] # Create a tuple of possible other languages child is exposed to


# Function for converting string 'True' into boolean True
def string_bool_coerce(val):
    return val == "True"


YESNO_CHOICES = ((False, _("No")), (True, _("Yes")))
YESNONA_CHOICES = ((0, _("No")), (1, _("Yes")), (2, _("Prefer not to disclose")))
INCOME_CHOICES = [
    ("", "--------"),
    ("<25000", _("Under $25,000")),
    ("25000-50000", _("$25,000-$50,000")),
    ("50000-75000", _("$50,000-$75,000")),
    ("75000-100000", _("$75,000-$100,000")),
    ("100000-125000", _("$100,000-$125,000")),
    ("125000-150000", _("$125,000-$150,000")),
    ("150000-175000", _("$150,000-$175,000")),
    ("175000-200000", _("$175,000-$200,000")),
    (">200000", _("Over $200,000")),
    ("Prefer not to disclose", _("Prefer not to disclose")),
]
CHILD_ETHNICITY_CHOICES = [
    ("N", _("American Indian / Alaska Native")),
    ("A", _("Asian (Far East, Southeast Asia, Indian Sub-continent)")),
    ("H", _("Native Hawaiian or Other Pacific Islander")),
    ("B", _("Black or African American")),
    ("W", _("White")),
    ("O", _("Other")),
]
# Declared set of birthweight choices (in lb and oz). Displays intervals instead of birthweight rounded down to nearest 0.5 lb
BIRTH_WEIGHT_LB_CHOICES = [
    ("", "--------"),
    (1.0, _("Less than 3 lbs, 0 oz")),
    (3.0, _("3 lbs, 0 oz - 3 lbs, 7 oz")),
    (3.5, _("3 lbs, 8 oz - 3 lbs, 15 oz")),
    (4.0, _("4 lbs, 0 oz - 4 lbs, 7 oz")),
    (4.5, _("4 lbs, 8 oz - 4 lbs, 15 oz")),
    (5.0, _("5 lbs, 0 oz - 5 lbs, 7 oz")),
    (5.5, _("5 lbs, 8 oz - 5 lbs, 15 oz")),
    (6.0, _("6 lbs, 0 oz - 6 lbs, 7 oz")),
    (6.5, _("6 lbs, 8 oz - 6 lbs, 15 oz")),
    (7.0, _("7 lbs, 0 oz - 7 lbs, 7 oz")),
    (7.5, _("7 lbs, 8 oz - 7 lbs, 15 oz")),
    (8.0, _("8 lbs, 0 oz - 8 lbs, 7 oz")),
    (8.5, _("8 lbs, 8 oz - 8 lbs, 15 oz")),
    (9.0, _("9 lbs, 0 oz - 9 lbs, 7 oz")),
    (9.5, _("9 lbs, 8 oz - 9 lbs, 15 oz")),
    (10.0, _("10 lbs, 0 oz or more")),
    (0.0, _("Prefer not to disclose")),
]

# Declared set of birthweight choices (in lb and oz). Displays intervals instead of birthweight rounded down to nearest 0.5 lb
BIRTH_WEIGHT_KG_CHOICES = [
    ("", "--------"),
    (1.00, _("Less than 1500 grams")),
    (1.50, _("1500 grams - 1749 grams")),
    (1.75, _("1750 grams - 1999 grams")),
    (2.00, _("2000 grams - 2249 grams")),
    (2.25, _("2250 grams - 2499 grams")),
    (2.50, _("2500 grams - 2749 grams")),
    (2.75, _("2750 grams - 2999 grams")),
    (3.00, _("3000 grams - 3249 grams")),
    (3.25, _("3250 grams - 3499 grams")),
    (3.50, _("3500 grams - 3749 grams")),
    (3.75, _("3750 grams - 3999 grams")),
    (4.00, _("4000 grams - 4249 grams")),
    (4.25, _("4250 grams - 4499 grams")),
    (4.50, _("4500 grams - 4749 grams")),
    (4.75, _("4750 grams - 4999 grams")),
    (5.00, _("5000 grams or more")),
    (0.00, _("Prefer not to disclose")),
]

EDUCATION_LEVELS = [
    (x, str(x)) for x in range(4, 25)
]  # Declares tuple of integers for # of years of education
# Appends additional text descriptions for years of education w/ milestones (high school diploma, bachelor's degree, and master's degree)
EDUCATION_LEVELS[12 - 5] = (12, _("12 (High school graduate)"))
EDUCATION_LEVELS[16 - 5] = (16, _("16 (College graduate)"))
EDUCATION_LEVELS[18 - 5] = (18, _("18 (Advanced degree)"))
EDUCATION_LEVELS[23 - 5] = (23, _("23 or more"))
EDUCATION_LEVELS[-1] = (0, _("Prefer not to disclose"))
EDUCATION_LEVELS[0] = ("", "--------")

EDUCATION_LEVELS = [
    ("", "--------"),
    (5, str(5)),
    (6, str(6)),
    (7, str(7)),
    (8, str(8)),
    (9, str(9)),
    (10, str(10)),
    (11, str(11)),
    (12, _("12 (High school graduate)")),
    (13, str(13)),
    (14, str(14)),
    (15, str(15)),
    (16, _("16 (College graduate)")),
    (17, str(17)),
    (18, _("18 (Advanced degree)")),
    (19, str(19)),
    (20, str(20)),
    (21, str(21)),
    (22, str(22)),
    (23, _("23 or more")),
    (0, _("Prefer not to disclose")),
]


# Form for asking about demographic variables for child. Most questions are required unless explicitly stated to be false.
class BackgroundForm(BetterModelForm):
    backpage = False

    sibling_boolean = forms.TypedChoiceField(
        choices=YESNO_CHOICES,
        widget=forms.RadioSelect,
        required=False,
        label=_("Does you child have siblings?"),
    )
    sibling_count = forms.IntegerField(
        required=False, label=_("How many siblings does you child have?")
    )
    sibling_data = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label=_("Please provide the sex and age of each sibling"),
    )

    # Child's DOB. Formatted weirdly to only be required if Age in months in not already stored in database.
    child_dob = forms.DateField(
        input_formats=["%m/%d/%Y"],
        widget=forms.TextInput(
            attrs={"max": datetime.datetime.now().strftime("%Y-%m-%d")}
        ),
        help_text=_(
            "To protect your privacy, we never store your child's date of birth, we only record age in months."
        ),
        validators=[MaxValueValidator(datetime.date.today())],
        label=mark_safe(_('Child DOB<span class="asteriskField">*</span>')),
        required=False,
    )

    # Child's age in months. Formatted weirdly to ask for 'child_dob' when empty.
    age = forms.IntegerField(
        label=mark_safe(_('Age (in months)<span class="asteriskField">*</span>')),
        validators=[MinValueValidator(0)],
        help_text=_(
            "This field will update when you enter or change your child's DOB."
        ),
        required=False,
    )

    # Zip code. Regex validation of zip code (3-digit prefix) occurs in models.py
    zip_code = forms.CharField(
        min_length=2,
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "XXXXX"}),
        label=_("What is your postal/zip code?"),
    )

    # Whether child is hispanic/latino. Yes/No question. Not required.
    child_hispanic_latino = forms.TypedChoiceField(
        choices=YESNO_CHOICES,
        widget=forms.RadioSelect,
        coerce=string_bool_coerce,
        required=False,
        label=_("Is your child Hispanic or Latino?"),
    )

    # Was child born early or late compared to due date. 2-choice question.
    early_or_late = forms.ChoiceField(
        choices=(("early", _("Early")), ("late", _("Late"))),
        widget=forms.RadioSelect,
        label=_("Was he/she early or late?"),
        required=False,
    )

    # Child's sex. Can choose M (male), F (female) or O (other/not disclosed)
    sex = forms.ChoiceField(
        choices=(
            ("M", _("Male")),
            ("F", _("Female")),
            ("O", _("Other")),
            ("P", _("Prefer not to disclose")),
        ),
        widget=forms.RadioSelect,
        label=_("Sex"),
    )

    # Multiple choice question. Choices are the languages listed in languages.json in root folder.
    other_languages = forms.MultipleChoiceField(
        choices=language_choices, label=_("Which language(s)"), required=False
    )

    form_filler_other = forms.CharField(
        label=" ",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Please specify")}),
    )

    primary_caregiver_other = forms.CharField(
        label=" ",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Please specify")}),
    )

    secondary_caregiver_other = forms.CharField(
        label=" ",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Please specify")}),
    )

    caregiver_other = forms.CharField(
        label=" ",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": pgettext_lazy("caregiver_other", "Please specify")}
        ),
    )

    # Cleaning input data for views.py and later database storage.
    def clean(self):
        cleaned_data = super(BackgroundForm, self).clean()
        # Nesting fields. Some questions, like 'born_on_due_date' trigger related subsequent questions like 'early_or_late' and 'due_date_diff' to inquire more depending on earlier answers.
        enabler_dependent_fields = (
            ("form_filler", ["form_filler_other"]),
            (
                "country",
                [
                    "zip_code",
                ],
            ),
            ("primary_caregiver", ["primary_caregiver_other"]),
            ("secondary_caregiver", ["secondary_caregiver_other"]),
            (
                "multi_birth_boolean",
                [
                    "multi_birth",
                ],
            ),
            (
                "born_on_due_date",
                [
                    "early_or_late",
                    "due_date_diff",
                ],
            ),
            (
                "other_languages_boolean",
                [
                    "other_languages",
                    "language_days_per_week",
                    "language_hours_per_day",
                    "language_from",
                ],
            ),
            ("sibling_boolean", ["sibling_count", "sibling_data"]),
            (
                "ear_infections_boolean",
                [
                    "ear_infections",
                ],
            ),
            (
                "hearing_loss_boolean",
                [
                    "hearing_loss",
                ],
            ),
            (
                "vision_problems_boolean",
                [
                    "vision_problems",
                ],
            ),
            (
                "illnesses_boolean",
                [
                    "illnesses",
                ],
            ),
            (
                "services_boolean",
                [
                    "services",
                ],
            ),
            (
                "worried_boolean",
                [
                    "worried",
                ],
            ),
            (
                "learning_disability_boolean",
                [
                    "learning_disability",
                ],
            ),
        )

        # If enabler field was answered as 'True', its related fields cannot be empty.
        for enabler, dependents in enabler_dependent_fields:
            enabler_val = cleaned_data.get(enabler)
            if enabler_val in ["1", "other", 1]:
                for dependent in dependents:
                    if (
                        dependent not in cleaned_data
                        or cleaned_data.get(dependent) == ""
                        or cleaned_data.get(dependent) is None
                    ):
                        self.add_error(dependent, _("This field cannot be empty"))

        # Check responses to 'early_or_late' and 'due_date_diff' to ensure biologically believable values.
        if (cleaned_data.get("early_or_late") in ["early", "late"]) and (
            cleaned_data["born_on_due_date"] == 1
        ):
            if not cleaned_data.get("due_date_diff"):
                self.add_error("born_on_due_date", _("Please enter number of weeks"))
            else:
                if (
                    cleaned_data.get("early_or_late") == "early"
                    and cleaned_data.get("due_date_diff") > 18
                ):
                    self.add_error(
                        "born_on_due_date", _("Cannot be more than 18 weeks early")
                    )
                if (
                    cleaned_data.get("early_or_late") == "late"
                    and cleaned_data.get("due_date_diff") > 4
                ):
                    self.add_error(
                        "born_on_due_date", _("Cannot be more than 4 weeks late")
                    )

        # Ensure that the 'age' field is not empty.
        if cleaned_data.get("age") == "":
            self.add_error(
                "age", _("Please enter your child's DOB in the field above.")
            )

        # Complex set of checks meant to ensure that there is an 'age' value stored in the database but 'DOB' is not. If there is no 'age' value in the database, enforce entry of 'child_dob'. If there is an age value, 'child_dob' is not necessary. Also check that 'age' is appropriate for the assigned Web-CDI form. Prevent continuing if not.
        c_dob = cleaned_data.get("child_dob")
        if c_dob:
            c_age = int((datetime.date.today() - c_dob).days / (365.2425 / 12.0))

        else:
            c_age = self.curr_context["child_age"]
        if c_age:
            if c_age < self.curr_context["min_age"]:
                self.add_error(
                    "age", _("Your baby is too young for this version of the CDI.")
                )
            elif c_age > (self.curr_context["max_age"]):
                self.add_error(
                    "age", _("Your baby is too old for this version of the CDI.")
                )
        else:
            self.add_error(
                "age", _("Please enter your child's DOB in the field above.")
            )

        if self.birth_weight_required:
            c_weight = cleaned_data.get(self.birth_weight_field)
            if not c_weight and c_weight != 0:
                self.add_error(self.birth_weight_field, _("This field cannot be empty"))

        return cleaned_data

    def get_json_filename(self):
        return get_demographic_filename(self.curr_context["study"])

    # Initiation of form. Set values, page format according to crispy forms, store variables delivered by views.py, and organize fields on the form.
    def __init__(self, *args, **kwargs):
        self.curr_context = kwargs.pop("context", None)
        self.filename = self.get_json_filename()
        self.page = kwargs.pop("page", False)
        super(BackgroundForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.template = "bootstrap/whole_uni_form.html"
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-3"
        self.helper.field_class = "col-lg-9"
        self.helper.form_method = "post"
        self.helper.form_tag = False

        self.fields["birth_weight_lb"].label = mark_safe(
            _("Birth weight") + '<span class="asteriskField">*</span>'
        )
        self.fields["birth_weight_kg"].label = mark_safe(
            _("Birth weight") + '<span class="asteriskField">*</span>'
        )

        self.fields["form_filler"].required = True
        self.fields["birth_order"].required = True

        # Whether child was a part of a multiple birth (twins, triplets, etc.)
        self.fields["multi_birth_boolean"].field = forms.TypedChoiceField
        self.fields["multi_birth_boolean"].choices = YESNONA_CHOICES
        self.fields["multi_birth_boolean"].widget = forms.RadioSelect()
        self.fields["multi_birth_boolean"].label = _(
            "Was your child born as part of a multiple birth?"
        )
        self.fields["multi_birth_boolean"].required = True

        # Was child born on their due date? Yes/No question.
        self.fields["born_on_due_date"].field = forms.TypedChoiceField
        self.fields["born_on_due_date"].choices = YESNONA_CHOICES
        self.fields["born_on_due_date"].widget = forms.RadioSelect()
        self.fields["born_on_due_date"].label = _(
            "Was your child born early or late (more than one week before or after the due date)?"
        )
        self.fields["born_on_due_date"].required = True

        self.fields["other_languages_boolean"].field = forms.TypedChoiceField
        self.fields["other_languages_boolean"].choices = YESNONA_CHOICES
        self.fields["other_languages_boolean"].widget = forms.RadioSelect()
        self.fields["other_languages_boolean"].label = _(
            "Does your child regularly hear a language other than English?"
        )
        self.fields["other_languages_boolean"].required = True

        self.fields["ear_infections_boolean"].field = forms.TypedChoiceField
        self.fields["ear_infections_boolean"].choices = YESNONA_CHOICES
        self.fields["ear_infections_boolean"].widget = forms.RadioSelect()
        self.fields["ear_infections_boolean"].label = _(
            "Has your child experienced chronic ear infections (5 or more)?"
        )
        self.fields["ear_infections_boolean"].required = True

        self.fields["hearing_loss_boolean"].field = forms.TypedChoiceField
        self.fields["hearing_loss_boolean"].choices = YESNONA_CHOICES
        self.fields["hearing_loss_boolean"].widget = forms.RadioSelect()
        self.fields["hearing_loss_boolean"].label = _(
            "Do you suspect that your child may have hearing loss?"
        )
        self.fields["hearing_loss_boolean"].required = True

        self.fields["vision_problems_boolean"].field = forms.TypedChoiceField
        self.fields["vision_problems_boolean"].choices = YESNONA_CHOICES
        self.fields["vision_problems_boolean"].widget = forms.RadioSelect()
        self.fields["vision_problems_boolean"].label = _(
            "Is there some reason to suspect that your child may have vision problems?"
        )
        self.fields["vision_problems_boolean"].required = True

        self.fields["illnesses_boolean"].field = forms.TypedChoiceField
        self.fields["illnesses_boolean"].choices = YESNONA_CHOICES
        self.fields["illnesses_boolean"].widget = forms.RadioSelect()
        self.fields["illnesses_boolean"].label = _(
            "Has your child had any major illnesses, hospitalizations, or diagnosed disabilities?"
        )
        self.fields["illnesses_boolean"].required = True

        self.fields["services_boolean"].field = forms.TypedChoiceField
        self.fields["services_boolean"].choices = YESNONA_CHOICES
        self.fields["services_boolean"].widget = forms.RadioSelect()
        self.fields["services_boolean"].label = _(
            "Has your child ever received any services for speech, language, or development issues?"
        )
        self.fields["services_boolean"].required = True

        self.fields["worried_boolean"].field = forms.TypedChoiceField
        self.fields["worried_boolean"].choices = YESNONA_CHOICES
        self.fields["worried_boolean"].widget = forms.RadioSelect()
        self.fields["worried_boolean"].label = _(
            "Are you worried about your child's progress in language or communication?"
        )
        self.fields["worried_boolean"].required = True

        self.fields["learning_disability_boolean"].field = forms.TypedChoiceField
        self.fields["learning_disability_boolean"].choices = YESNONA_CHOICES
        self.fields["learning_disability_boolean"].widget = forms.RadioSelect()
        self.fields["learning_disability_boolean"].label = _(
            "Have you or anyone in your immediate family been diagnosed with a language or learning disability?"
        )
        self.fields["learning_disability_boolean"].required = True

        self.fields["primary_caregiver"].required = True
        self.fields["mother_yob"].required = True
        self.fields["mother_yob_confirmation"].required = False
        self.fields["mother_education"].required = True
        self.fields["mother_education"].choices = EDUCATION_LEVELS
        self.fields["father_education"].choices = EDUCATION_LEVELS

        self.fields["annual_income"].required = True
        self.fields["caregiver_info"].required = True

        self.fields["birth_weight_lb"].field = forms.TypedChoiceField
        self.fields["birth_weight_kg"].field = forms.TypedChoiceField

        try:
            self.fields["country"].initial = settings.LANGUAGE_TO_COUNTRY_DICT[
                self.curr_context["language"]
            ].upper()
        except:
            pass

        self.birth_weight_required = True
        if self.curr_context["birthweight_units"] == "lb":
            self.birth_weight_field = "birth_weight_lb"
        elif self.curr_context["birthweight_units"] == "kg":
            self.birth_weight_field = "birth_weight_kg"
        else:
            self.birth_weight_required = False

        if self.curr_context["language"] in ["English", "Spanish"]:
            self.fields["child_dob"].input_formats = (
                "%m/%d/%Y",
                "%m/%d/%y",
            )
            self.fields["child_dob"].widget.attrs["placeholder"] = _("mm/dd/yyyy")
        else:
            self.fields["child_dob"].input_formats = (
                "%d/%m/%Y",
                "%d/%m/%y",
            )
            self.fields["child_dob"].widget.attrs["placeholder"] = _("dd/mm/yyyy")

        if self.curr_context["study"].hide_source_id:
            self.fields["source_id"].widget = forms.HiddenInput()

        # if we have a specified background info, use it
        if os.path.isfile(self.filename):
            rows = []
            hidden_fields = []
            selected_fields = []
            pages = json.load(open(self.filename, encoding="utf-8"))
            for page in pages:
                if page["page"] == self.page:
                    selected_fields = []
                    fieldsets = page["contents"]
                    for fieldset in fieldsets:
                        fields = []
                        if "html" in fieldset:
                            fields.append(HTML(fieldset["html"]))
                        for field in fieldset["fields"]:
                            if "field" in field:
                                selected_fields.append(field["field"])
                            if "widget_type" in field:
                                if field["widget_type"] == "Select":
                                    self.fields[field["field"]].widget = forms.Select()
                                if field["widget_type"] == "CheckboxSelectMultiple":
                                    self.fields[
                                        field["field"]
                                    ].widget = forms.CheckboxSelectMultiple()
                                if field["widget_type"] == "RadioSelect":
                                    self.fields[
                                        field["field"]
                                    ].widget = forms.RadioSelect()
                                    self.fields[field["field"]].choices = self.fields[
                                        field["field"]
                                    ].choices[1:]
                            if "label" in field:
                                self.fields[field["field"]].label = field["label"]
                            if "choices" in field:
                                choices = []
                                for choice in field["choices"]:
                                    choices.append((choice["key"], choice["value"]))
                                self.fields[field["field"]].widget.choices = choices
                                self.fields[field["field"]].choices = choices
                                self.initial[field["field"]] = getattr(
                                    self.instance, field["field"]
                                )
                            if "help" in field:
                                self.fields[field["field"]].help_text = field["help"]
                            if "required" in field:
                                self.fields[field["field"]].required = True
                            if "html" in field:
                                fields.append(HTML(field["html"]))
                            if "divs" in field:
                                fields.append(
                                    Field(field["field"], css_class="enabler")
                                )
                                for div in field["divs"]:
                                    fields.append(
                                        Div(
                                            Field(div["field"], css_class=div["css"]),
                                            *div["div"],
                                            css_class="dependent"
                                        )
                                    )
                                    selected_fields.append(div["field"])
                                    if "choices" in div:
                                        choices = []
                                        for choice in div["choices"]:
                                            choices.append(
                                                (choice["key"], choice["value"])
                                            )
                                        self.fields[
                                            div["field"]
                                        ].widget.choices = choices
                                        self.fields[div["field"]].choices = choices
                                        self.initial[div["field"]] = getattr(
                                            self.instance, div["field"]
                                        )
                                    for item in div["div"]:
                                        selected_fields.append(item)
                            elif "div" in field:
                                fields.append(
                                    Field(field["field"], css_class="enabler")
                                )
                                fields.append(Div(*field["div"], css_class="dependent"))
                                for f in field["div"]:
                                    selected_fields.append(f)
                            else:
                                if "field" in field:
                                    fields.append(field["field"])
                        if "HTML" in fieldset:
                            rows.append(
                                Fieldset(
                                    fieldset["fieldset"],
                                    HTML(fieldset["HTML"]),
                                    *fields
                                )
                            )
                        else:
                            rows.append(Fieldset(fieldset["fieldset"], *fields))
                else:
                    fieldsets = page["contents"]
                    for fieldset in fieldsets:
                        for field in fieldset["fields"]:
                            if "field" in field:
                                hidden_fields.append(field["field"])
                                self.fields[field["field"]].widget = forms.HiddenInput()
                            if "widget_type" in field:
                                if field["widget_type"] == "CheckboxSelectMultiple":
                                    self.fields[
                                        field["field"]
                                    ].widget = forms.MultipleHiddenInput()
                            if "choices" in field:
                                choices = []
                                for choice in field["choices"]:
                                    choices.append((choice["key"], choice["value"]))
                                self.fields[field["field"]].widget.choices = choices
                                self.fields[field["field"]].choices = choices
                                self.initial[field["field"]] = getattr(
                                    self.instance, field["field"]
                                )
                            if "divs" in field:
                                for div in field["divs"]:
                                    hidden_fields.append(div["field"])
                                    self.fields[
                                        div["field"]
                                    ].widget = forms.HiddenInput()
                                    if "css" in div:
                                        if div["css"] == "make-selectize":
                                            self.fields[
                                                div["field"]
                                            ].widget = forms.MultipleHiddenInput()

                                    if "choices" in div:
                                        choices = []
                                        for choice in div["choices"]:
                                            choices.append(
                                                (choice["key"], choice["value"])
                                            )
                                        self.fields[
                                            div["field"]
                                        ].widget.choices = choices
                                        self.fields[div["field"]].choices = choices
                                        self.initial[div["field"]] = getattr(
                                            self.instance, div["field"]
                                        )

                                    for item in div["div"]:
                                        hidden_fields.append(item)
                                        self.fields[item].widget = forms.HiddenInput()
                            elif "div" in field:
                                for f in field["div"]:
                                    hidden_fields.append(f)
                                    self.fields[f].widget = forms.HiddenInput()
                    for field in hidden_fields:
                        self.fields[field].required = False
                    rows.append(Fieldset("", *hidden_fields))

            # now remove required from any standard fields not included
            more_hidden_fields = []
            for x in self.fields:
                if x not in selected_fields and x not in hidden_fields:
                    self.fields[x].required = False
                    more_hidden_fields.append(x)
                    self.fields[x].widget = forms.HiddenInput()
                    if x == "other_languages":
                        self.fields[x].widget = forms.MultipleHiddenInput()
            rows.append(Fieldset("", *more_hidden_fields))
            self.helper.layout = Layout(*rows)

            if "birth_weight_lb" in selected_fields:
                self.birth_weight_required = True
                if len(self.fields["birth_weight_lb"].widget.choices) < 1:
                    self.fields[
                        "birth_weight_lb"
                    ].widget.choices = BIRTH_WEIGHT_LB_CHOICES
            elif "birth_weight_kg" in selected_fields:
                self.birth_weight_required = True
                if len(self.fields["birth_weight_kg"].widget.choices) < 1:
                    self.fields[
                        "birth_weight_kg"
                    ].widget.choices = BIRTH_WEIGHT_KG_CHOICES
            else:
                self.birth_weight_required = False

            if "birth_weight_confirmation_lb" in selected_fields:
                if len(self.fields["birth_weight_confirmation_lb"].widget.choices) < 1:
                    self.fields[
                        "birth_weight_confirmation_lb"
                    ].widget.choices = BIRTH_WEIGHT_LB_CHOICES
            if "birth_weight_confirmation_kg" in selected_fields:
                if len(self.fields["birth_weight_confirmation_kg"].widget.choices) < 1:
                    self.fields[
                        "birth_weight_confirmation_kg"
                    ].widget.choices = BIRTH_WEIGHT_KG_CHOICES
            try:
                if not self.curr_context["study"].confirmation_questions:
                    self.fields[
                        "birth_weight_confirmation_lb"
                    ].widget = forms.HiddenInput()
                    self.fields[
                        "birth_weight_confirmation_kg"
                    ].widget = forms.HiddenInput()
                    self.fields["mother_yob_confirmation"].widget = forms.HiddenInput()
            except:
                pass

            if "annual_income" in selected_fields:
                if len(self.fields["annual_income"].widget.choices) < 1:
                    self.fields["annual_income"].widget.choices = INCOME_CHOICES

        # otherwise use the standard format
        else:
            self.fields["birth_weight_lb"].widget = forms.Select()
            self.fields["birth_weight_lb"].widget.choices = BIRTH_WEIGHT_LB_CHOICES
            self.fields["birth_weight_kg"].widget = forms.Select()
            self.fields["birth_weight_kg"].widget.choices = BIRTH_WEIGHT_KG_CHOICES
            self.fields["annual_income"] = forms.ChoiceField(choices=INCOME_CHOICES)
            self.fields["annual_income"].label = _(
                "Estimated Annual Family Income (in USD)"
            )
            self.fields["child_ethnicity"] = forms.MultipleChoiceField(
                choices=CHILD_ETHNICITY_CHOICES
            )
            self.fields["child_ethnicity"].widget = forms.CheckboxSelectMultiple()
            self.fields["child_ethnicity"].required = False
            self.fields["child_ethnicity"].label = _(
                "My child is (check all that apply):"
            )

            if self.curr_context["study"].participant_source_boolean > 0:
                basic_info_fieldset = Fieldset(
                    _("Basic Information"),
                    Field("form_filler", css_class="enabler"),
                    Div("form_filler_other", css_class="dependent"),
                    "source_id",
                    "child_dob",
                    "age",
                    "sex",
                    Field("country", css_class="enabler"),
                    Div("zip_code", css_class="dependent"),
                    "birth_order",
                    Field("multi_birth_boolean", css_class="enabler"),
                    Div("multi_birth", css_class="dependent"),
                    self.birth_weight_field,
                    Field("born_on_due_date", css_class="enabler"),
                    Div("early_or_late", "due_date_diff", css_class="dependent"),
                )
            else:
                basic_info_fieldset = Fieldset(
                    _("Basic Information"),
                    Field("form_filler", css_class="enabler"),
                    Div("form_filler_other", css_class="dependent"),
                    "child_dob",
                    "age",
                    "sex",
                    Field("country", css_class="enabler"),
                    Div("zip_code", css_class="dependent"),
                    "birth_order",
                    Field("multi_birth_boolean", css_class="enabler"),
                    Div("multi_birth", css_class="dependent"),
                    self.birth_weight_field,
                    Field("born_on_due_date", css_class="enabler"),
                    Div("early_or_late", "due_date_diff", css_class="dependent"),
                )
                self.fields["source_id"].widget = forms.HiddenInput()
            self.helper.layout = Layout(
                basic_info_fieldset,
                Fieldset(
                    _("Family Background"),
                    Field("primary_caregiver", css_class="enabler"),
                    Div("primary_caregiver_other", css_class="dependent"),
                    "mother_yob",
                    "mother_education",
                    Field("secondary_caregiver", css_class="enabler"),
                    Div("secondary_caregiver_other", css_class="dependent"),
                    "father_yob",
                    "father_education",
                    "annual_income",
                ),
                Fieldset(
                    _("Child's Ethnicity"),
                    HTML(
                        "<p> "
                        + gettext(
                            "The following information is being collected for the sole purpose of reporting to our grant-funding institute, i.e.,  NIH (National Institute of Health).  NIH requires this information to ensure the soundness and inclusiveness of our research. Your cooperation is appreciated, but optional."
                        )
                        + " </p>"
                    ),
                    "child_hispanic_latino",
                    "child_ethnicity",
                ),
                Fieldset(
                    _("Caregiver Information"),
                    Field("caregiver_info", css_class="enabler"),
                    Div("caregiver_other", css_class="dependent"),
                ),
                Fieldset(
                    _("Language Exposure"),
                    Field("other_languages_boolean", css_class="enabler"),
                    Div(
                        Field("other_languages", css_class="make-selectize"),
                        "language_from",
                        "language_days_per_week",
                        "language_hours_per_day",
                        css_class="dependent",
                    ),
                ),
                Fieldset(
                    _("Health"),
                    Field("ear_infections_boolean", css_class="enabler"),
                    Div("ear_infections", css_class="dependent"),
                    Field("hearing_loss_boolean", css_class="enabler"),
                    Div("hearing_loss", css_class="dependent"),
                    Field("vision_problems_boolean", css_class="enabler"),
                    Div("vision_problems", css_class="dependent"),
                    Field("illnesses_boolean", css_class="enabler"),
                    Div("illnesses", css_class="dependent"),
                    Field("services_boolean", css_class="enabler"),
                    Div("services", css_class="dependent"),
                    Field("worried_boolean", css_class="enabler"),
                    Div("worried", css_class="dependent"),
                    Field("learning_disability_boolean", css_class="enabler"),
                    Div("learning_disability", css_class="dependent"),
                ),
            )

        if self.curr_context["source_id"] is not None:
            self.fields["source_id"].initial = self.curr_context["source_id"]
            if self.fields["source_id"].initial == "None":
                self.fields["source_id"].initial = ""

        if not self.curr_context["study_obj"].participant_source_boolean:
            self.fields["source_id"].widget = forms.HiddenInput()
        else:
            self.fields["source_id"].label = _("Your identifier for %(source)s") % {
                "source": self.curr_context[
                    "study_obj"
                ].get_participant_source_boolean_display()
            }

    # Link form to BackgroundInfo model stored in database. Declare widget formatting for specific fields.
    class Meta:
        model = BackgroundInfo
        exclude = ["administration"]

        widgets = {
            "ear_infections": forms.Textarea(attrs={"cols": 80, "rows": 3}),
            "hearing_loss": forms.Textarea(attrs={"cols": 80, "rows": 3}),
            "vision_problems": forms.Textarea(attrs={"cols": 80, "rows": 3}),
            "illnesses": forms.Textarea(attrs={"cols": 80, "rows": 3}),
            "services": forms.Textarea(attrs={"cols": 80, "rows": 3}),
            "worried": forms.Textarea(attrs={"cols": 80, "rows": 3}),
            "learning_disability": forms.Textarea(attrs={"cols": 80, "rows": 3}),
            "due_date_diff": forms.NumberInput(attrs={"min": "1", "max": "18"}),
        }


# we want all the functionality of the BackgroundForm on the backpage, without redefining it
class BackpageBackgroundForm(BackgroundForm):
    backpage = True
