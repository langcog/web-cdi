from django.conf import settings
from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Field, Row, Div, HTML
from crispy_forms.bootstrap import InlineField
from form_utils.forms import BetterModelForm
from django.templatetags.static import static
import datetime, codecs, json, os.path
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext



PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__)) # Declare project file directory

isoLangs = json.load(codecs.open(PROJECT_ROOT + '/../' + 'languages.json', 'r', 'utf-8')) # Load up languages stored in languages.json in project root for other_languages question

language_choices = [(v['name'],v['nativeName'] + " ("+ v['name'] + ")") for k,v in isoLangs.iteritems()] # Create a tuple of possible other languages child is exposed to

# Function for converting string 'True' into boolean True
def string_bool_coerce(val):
    return val == 'True'

# Form for asking about demographic variables for child. Most questions are required unless explicitly stated to be false.
class BackgroundForm(BetterModelForm):

    # Multiple checkbox question regarding child's ethnicity. Not required.
    child_ethnicity = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
    choices = (
    ('N', _("American Indian / Alaska Native")),
    ('A', _("Asian (Far East, Southeast Asia, Indian Sub-continent)")), 
    ('H', _("Native Hawaiian or Other Pacific Islander")),
    ('B', _("Black or African American")),
    ('W', _("White")),
    ('O', _("Other"))), label = _("My child is (check all that apply):"), required = False)
    YESNO_CHOICES = ((False, _('No')), (True, _('Yes')))
    YESNONA_CHOICES = ((0, _('No')), (1, _('Yes')), (2, _('Prefer not to disclose')))

    # Child's DOB. Formatted weirdly to only be required if Age in months in not already stored in database.
    child_dob = forms.DateField(input_formats=['%m/%d/%Y'], widget=forms.TextInput(),
                                help_text = _("To protect your privacy, we never store your child's date of birth, we only record age in months."),
                                validators = [MaxValueValidator(datetime.date.today())], label = _('Child DOB<span class="asteriskField">*</span>'), required=False)

    # Child's age in months. Formatted weirdly to ask for 'child_dob' when empty.
    age = forms.IntegerField(label = _('Age (in months)<span class="asteriskField">*</span>'), validators=[MinValueValidator(0)], help_text=_('This field will update when you enter or change your child\'s DOB.'), required=False)

    # Zip code. Regex validation of zip code (3-digit prefix) occurs in models.py
    zip_code = forms.CharField(min_length = 2, max_length = 5, required = False, widget=forms.TextInput(attrs={'placeholder': 'XXXXX'}), label = _("What is your zip code?<br>(if you live in the U.S.)"))

    # Whether child is hispanic/latino. Yes/No question. Not required.
    child_hispanic_latino = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce = string_bool_coerce
                , required=False, label=_("Is your child Hispanic or Latino?"))

    # Was child born on their due date? Yes/No question.
    born_on_due_date = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, label=_('Was your child born early or late (more than one week before or after the due date)?'))
    
    # Was child born early or late compared to due date. 2-choice question. 
    early_or_late = forms.ChoiceField(
                     choices=(('early', _('Early')),('late', _('Late'))), widget=forms.RadioSelect, label=_("Was he/she early or late?"),
                 required=False)

    # Child's sex. Can choose M (male), F (female) or O (other/not disclosed)
    sex = forms.ChoiceField(
                     choices=(('M', _('Male')), ('F', _('Female')), ('O', _('Other / Prefer not to disclose'))), widget=forms.RadioSelect,
                     label=_('Sex')
                )

    # Whether child was a part of a multiple birth (twins, triplets, etc.)
    multi_birth_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, label=_("Was your child born as part of a multiple birth?"))

    # Whether child is exposed to other languages (currently besides English)
    other_languages_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, label=_('Does your child regularly hear a language other than English?'))

    # Whether child experienced 5+ ear infections
    ear_infections_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect,
                     label =  
                     _("Has your child experienced chronic ear infections (5 or more)?")
                     )

    # Whether child may suffer from hearing loss
    hearing_loss_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        _('Do you suspect that your child may have hearing loss?') 
                     )

    # Whether child may have vision problems
    vision_problems_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        _('Is there some reason to suspect that your child may have vision problems?') 
                     )

    #Whether child may have major illnesses, hospitalizations, or diagnoses
    illnesses_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                         _('Has your child had any major illnesses, hospitalizations, or diagnosed disabilities?') 
                     )

    # Whether child has received services for speech or language
    services_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        _('Has your child ever received any services for speech, language, or development issues?') 
                     )

    # Whether test-taker has concerns about child's language development
    worried_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        _('Are you worried about your child\'s progress in language or communication?') 
                     )

    # Whether child has a relative diagnoses with a language/learning disability
    learning_disability_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        _('Have you or anyone in your immediate family been diagnosed with a language or learning disability?') 
                     )

    # Multiple choice question. Choices are the languages listed in languages.json in root folder.
    other_languages = forms.MultipleChoiceField(
                     choices=language_choices, 
                     label = _("Which language(s)"), required = False
                )

    # Cleaning input data for views.py and later database storage.
    def clean(self):
        cleaned_data = super(BackgroundForm, self).clean()
        
        # Nesting fields. Some questions, like 'born_on_due_date' trigger related subsequent questions like 'early_or_late' and 'due_date_diff' to inquire more depending on earlier answers.
        enabler_dependent_fields = (
        ('multi_birth_boolean', ['multi_birth',]),
        ('born_on_due_date', ['early_or_late', 'due_date_diff',]),
        ('other_languages_boolean', ['other_languages', 'language_days_per_week', 'language_hours_per_day', 'language_from']),
        ('ear_infections_boolean', ['ear_infections',]),
        ('hearing_loss_boolean', ['hearing_loss',]),
        ('vision_problems_boolean', ['vision_problems',]),
        ('illnesses_boolean', ['illnesses',]),
        ('services_boolean', ['services',]),
        ('worried_boolean', ['worried',]),
        ('learning_disability_boolean', ['learning_disability',]),)

        # If enabler field was answered as 'True', its related fields cannot be empty. 
        for (enabler, dependents) in enabler_dependent_fields:
            enabler_val = cleaned_data.get(enabler)
            if enabler_val == '1':
                for dependent in dependents:
                    if dependent not in cleaned_data or cleaned_data.get(dependent) == '':
                        self.add_error(dependent, _("This field cannot be empty"))
        
        # Check responses to 'early_or_late' and 'due_date_diff' to ensure biologically believable values.
        if cleaned_data.get('early_or_late') == 'early' and cleaned_data.get('due_date_diff') > 18:
            self.add_error(dependent, _("Cannot be more than 18 weeks early"))
        if cleaned_data.get('early_or_late') == 'late' and cleaned_data.get('due_date_diff') > 4:
            self.add_error(dependent, _("Cannot be more than 4 weeks late"))
        
        # Ensure that the 'age' field is not empty.
        if cleaned_data.get('age') == '':
            self.add_error('age', _('Please enter your child\'s DOB in the field above.'))

        # Complex set of checks meant to ensure that there is an 'age' value stored in the database but 'DOB' is not. If there is no 'age' value in the database, enforce entry of 'child_dob'. If there is an age value, 'child_dob' is not necessary. Also check that 'age' is appropriate for the assigned Web-CDI form. Prevent continuing if not.
        c_dob = cleaned_data.get('child_dob')
        if c_dob:
            day_diff = datetime.date.today().day - c_dob.day
            c_age = (datetime.date.today().year - c_dob.year) * 12 +  (datetime.date.today().month - c_dob.month) + (1 if day_diff >=15 else 0)
        else:
            c_age = self.curr_context['child_age']
        if c_age:
            if c_age < self.curr_context['min_age']:
                self.add_error('age', _('Your baby is too young for this version of the CDI.'))
            elif c_age > (self.curr_context['max_age']):
                self.add_error('age', _('Your baby is too old for this version of the CDI.'))
        else:
            self.add_error('age', _('Please enter your child\'s DOB in the field above.'))
        c_weight = cleaned_data.get(self.birth_weight_field)
        if not c_weight and c_weight != 0:
            self.add_error(self.birth_weight_field, _('This field cannot be empty'))



    #Initiation of form. Set values, page format according to crispy forms, store variables delivered by views.py, and organize fields on the form.
    def __init__(self, *args, **kwargs):
        self.curr_context = kwargs.pop('context', None)
        super(BackgroundForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.template = PROJECT_ROOT + '/templates/bootstrap/whole_uni_form.html'
        self.helper.form_class = 'form-inline'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.form_method = 'post'

        self.fields['birth_weight_lb'].label = _('Birth weight') + '<span class="asteriskField">*</span>'
        self.fields['birth_weight_kg'].label = _('Birth weight') + '<span class="asteriskField">*</span>'

        if self.curr_context['birthweight_units'] == "lb":
            self.birth_weight_field = 'birth_weight_lb'
        elif self.curr_context['birthweight_units'] == "kg":
            self.birth_weight_field = 'birth_weight_kg'

        if self.curr_context['language'] == "English":
            self.fields['child_dob'].input_formats = ('%m/%d/%Y', '%m/%d/%y',)
            self.fields['child_dob'].widget.attrs['placeholder'] = 'mm/dd/yyyy'
        else:
            self.fields['child_dob'].input_formats = ('%d/%m/%Y', '%d/%m/%y',)
            self.fields['child_dob'].widget.attrs['placeholder'] = 'dd/mm/yyyy'

        self.helper.layout = Layout(
            Fieldset( _('Basic Information'), 'child_dob','age', 'sex','zip_code','birth_order', Field('multi_birth_boolean', css_class='enabler'), Div('multi_birth', css_class='dependent'), self.birth_weight_field, Field('born_on_due_date', css_class='enabler'), Div('early_or_late', 'due_date_diff', css_class='dependent')),
            Fieldset( _('Family Background'), 'mother_yob', 'mother_education','father_yob', 'father_education', 'annual_income'),
            Fieldset( _("Child's Ethnicity"),HTML("<p> " + ugettext("The following information is being collected for the sole purpose of reporting to our grant-funding institute, i.e.,  NIH (National Institute of Health).  NIH requires this information to ensure the soundness and inclusiveness of our research. Your cooperation is appreciated, but optional.") + " </p>"), 'child_hispanic_latino', 'child_ethnicity'),
            Fieldset( _("Caregiver Information"), 'caregiver_info'),
            Fieldset( _("Language Exposure"), Field('other_languages_boolean', css_class = 'enabler'), Div(Field('other_languages', css_class='make-selectize'),'language_from', 'language_days_per_week', 'language_hours_per_day', css_class='dependent')),
            Fieldset( _("Health"), 
            Field('ear_infections_boolean', css_class = 'enabler'), Div('ear_infections', css_class='dependent'),
            Field('hearing_loss_boolean', css_class = 'enabler'), Div('hearing_loss', css_class='dependent'),
            Field('vision_problems_boolean', css_class = 'enabler'), Div('vision_problems', css_class='dependent'),
            Field('illnesses_boolean', css_class = 'enabler'), Div('illnesses', css_class='dependent'),
            Field('services_boolean', css_class = 'enabler'), Div('services', css_class='dependent'),
            Field('worried_boolean', css_class = 'enabler'), Div('worried', css_class='dependent'),
            Field('learning_disability_boolean', css_class = 'enabler'), Div('learning_disability', css_class='dependent'),),

)

    #Link form to BackgroundInfo model stored in database. Declare widget formatting for specific fields.
    class Meta:
        model = BackgroundInfo
        exclude = ['administration']
        
        widgets = { 
        'ear_infections': forms.Textarea(attrs={'cols': 80, 'rows': 3}), 
        'hearing_loss': forms.Textarea(attrs={'cols': 80, 'rows': 3}), 
        'vision_problems': forms.Textarea(attrs={'cols': 80, 'rows': 3}), 
        'illnesses': forms.Textarea(attrs={'cols': 80, 'rows': 3}), 
        'services': forms.Textarea(attrs={'cols': 80, 'rows': 3}), 
        'worried': forms.Textarea(attrs={'cols': 80, 'rows': 3}), 
        'learning_disability': forms.Textarea(attrs={'cols': 80, 'rows': 3}), 
        'due_date_diff': forms.NumberInput(attrs={'min':'1', 'max':'18'})
        }

# Form for contacting Web-CDI team. Asks for basic contact information and test ID. Simple format.
class ContactForm(forms.Form):
    contact_name = forms.CharField(label=_("Your Name"), required=True, max_length = 51)
    contact_email = forms.EmailField(label=_("Your Email Address"), required=True, max_length = 201, validators = [EmailValidator()])
    contact_id = forms.CharField(label=_("Your Test URL"), required=True, max_length = 101)
    content = forms.CharField(label=_("What would you like to tell us?"),
        required=True,
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 6}),
        max_length = 1001
    )

    def __init__(self, *args, **kwargs):
        self.redirect_url = kwargs.pop('redirect_url', '')
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['contact_id'].initial=self.redirect_url
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            Field('contact_name'), 
            Field('contact_email'), 
            Field('contact_id', css_class = "form-control-plaintext"), 
            Field('content'), 
            Div(Submit('submit','Submit'), css_class="col-lg-offset-3 col-lg-9 text-center"))
