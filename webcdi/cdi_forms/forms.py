from django.conf import settings

from django.forms import ModelForm, Textarea
from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Field, Row, Div, HTML
from crispy_forms.bootstrap import InlineField
from form_utils.forms import BetterModelForm
from django.templatetags.static import static
import datetime
from django.core.exceptions import ValidationError
import codecs, json
import os.path
from django.core.validators import EmailValidator, RegexValidator

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

isoLangs = json.load(codecs.open(PROJECT_ROOT + '/../' + 'languages.json', 'r', 'utf-8'))

language_choices = [(v['name'],v['name']) for k,v in isoLangs.iteritems()]

def string_bool_coerce(val):
    return val == 'True'

class BackgroundForm(BetterModelForm):
    child_ethnicity = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
    choices = (
    ('N', "American Indian / Alaska Native"),
    ('A', "Asian (Far East, Southeast Asia, Indian Sub-continent)"), 
    ('H', "Native Hawaiian or Other Pacific Islander"),
    ('B', "Black or African American"),
    ('W', "White"),
    ('O', "Other")), label = "My child is (check all that apply):", required = False)
    YESNO_CHOICES = ((False, 'No'), (True, 'Yes'))
    YESNONA_CHOICES = ((0, 'No'), (1, 'Yes'), (2, 'Prefer not to disclose'))

    child_dob = forms.DateField(input_formats=['%m/%d/%Y'], widget=forms.TextInput(attrs={'placeholder': 'mm/dd/yyyy'}),
                                help_text = "To protect your privacy, we never store your child's date of birth, we only record age in months.",
                                validators = [MaxValueValidator(datetime.date.today())], label = 'Child DOB<span class="asteriskField">*</span>', required=False)

    age = forms.IntegerField(label = 'Age (in months)<span class="asteriskField">*</span>', validators=[MinValueValidator(0)], help_text='This field will update when you enter or change your child\'s DOB.', required=False)

    zip_code = forms.CharField(min_length = 5, max_length = 5, required = False, widget=forms.TextInput(attrs={'placeholder': 'XXXXX'}), label = "What is your zip code?<br>(if you live in the U.S.)")

    child_hispanic_latino = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce = string_bool_coerce
                , required=False, label="Is your child Hispanic or Latino?")
    born_on_due_date = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, label='Was your child born early or late (more than one week before or after the due date)?')
    early_or_late = forms.ChoiceField(
                     choices=(('early', 'Early'),('late', 'Late')), widget=forms.RadioSelect,
                 required=False)
    sex = forms.ChoiceField(
                     choices=(('M', 'Male'), ('F', 'Female'), ('O', 'Other / Prefer not to disclose')), widget=forms.RadioSelect,
                )
    other_languages_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, label='Does your child regularly hear a language other than English?')

    ear_infections_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect,
                     label =  
                     "Has your child experienced chronic ear infections (5 or more)?"
                     )
    hearing_loss_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        'Do you suspect that your child may have hearing loss?' 
                     )
    vision_problems_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        'Is there some reason to suspect that your child may have vision problems?' 
                     )
    illnesses_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                         'Has your child had any major illnesses, hospitalizations, or diagnosed disabilities?' 
                     )
    services_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        'Has your child ever received any services for speech, language, or development issues?' 
                     )
    worried_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        'Are you worried about your child\'s progress in language or communication?' 
                     )
    learning_disability_boolean = forms.TypedChoiceField(
                     choices=YESNONA_CHOICES, widget=forms.RadioSelect, 
                     label =  
                        'Have you or anyone in your immediate family been diagnosed with a language or learning disability?' 
                     )
    other_languages = forms.MultipleChoiceField(
                     choices=language_choices, 
                     label = "Which language(s)", required = False
                )
    #birth_order = forms.IntegerField(label = "Birth order (enter number e.g., 1 for first)")

    def clean(self):
        cleaned_data = super(BackgroundForm, self).clean()
        enabler_dependent_fields = (
        ('born_on_due_date', ['early_or_late', 'due_date_diff',]),
        ('other_languages_boolean', ['other_languages', 'language_days_per_week', 'language_hours_per_day', 'language_from']),
        ('ear_infections_boolean', ['ear_infections',]),
        ('hearing_loss_boolean', ['hearing_loss',]),
        ('vision_problems_boolean', ['vision_problems',]),
        ('illnesses_boolean', ['illnesses',]),
        ('services_boolean', ['services',]),
        ('worried_boolean', ['worried',]),
        ('learning_disability_boolean', ['learning_disability',]),)
        for (enabler, dependents) in enabler_dependent_fields:
            enabler_val = cleaned_data.get(enabler)
            if enabler_val == '1':
                for dependent in dependents:
                    if dependent not in cleaned_data or cleaned_data.get(dependent) == '':
                        self.add_error(dependent, "This field cannot be empty")
        if cleaned_data.get('early_or_late') == 'early' and cleaned_data.get('due_date_diff') > 18:
            self.add_error(dependent, "Cannot be more than 18 weeks early")
        if cleaned_data.get('early_or_late') == 'late' and cleaned_data.get('due_date_diff') > 4:
            self.add_error(dependent, "Cannot be more than 4 weeks late")
        if cleaned_data.get('age') == '':
            self.add_error('age', 'Please enter your child\'s DOB in the field above.')

        c_dob = cleaned_data.get('child_dob')
        if c_dob:
            day_diff = datetime.date.today().day - c_dob.day
            c_age = (datetime.date.today().year - c_dob.year) * 12 +  (datetime.date.today().month - c_dob.month) + (1 if day_diff >=15 else 0)
        else:
            c_age = self.age_ref['child_age']
        if c_age:
            if c_age < self.age_ref['min_age']:
                self.add_error('age', 'Your baby is too young for this version of the CDI.')
            elif c_age > (self.age_ref['max_age']):
                self.add_error('age', 'Your baby is too old for this version of the CDI.')
        else:
            self.add_error('age', 'Please enter your child\'s DOB in the field above.')




    def __init__(self, *args, **kwargs):
        self.age_ref = kwargs.pop('age_ref', None)
        super(BackgroundForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.form_method = 'post'

        #LINE BELOW ADDED AS A TEST TO FIX THE DATE ISSUE
        self.fields['child_dob'].input_formats=(settings.DATE_INPUT_FORMATS)
        self.helper.layout = Layout(
            Fieldset( 'Basic Information', 'child_dob','age', 'sex','zip_code','birth_order', 'birth_weight', Field('born_on_due_date', css_class='enabler'), Div('early_or_late', 'due_date_diff', css_class='dependent')),
            Fieldset( 'Family Background', 'mother_yob', 'mother_education','father_yob', 'father_education', 'annual_income'),
            Fieldset( "Child's Ethnicity",HTML("<p> The following information is being collected for the sole purpose of reporting to our grant-funding institute, i.e.,  NIH (National Institute of Health).  NIH requires this information to ensure the soundness and inclusiveness of our research. Your cooperation is appreciated, but optional. </p>"), 'child_hispanic_latino', 'child_ethnicity'),
            Fieldset( "Caregiver Information", 'caregiver_info'),
            Fieldset( "Language Exposure", Field('other_languages_boolean', css_class = 'enabler'), Div(Field('other_languages', css_class='make-selectize'),'language_from', 'language_days_per_week', 'language_hours_per_day', css_class='dependent')),
            Fieldset( "Health", 
            Field('ear_infections_boolean', css_class = 'enabler'), Div('ear_infections', css_class='dependent'),
            Field('hearing_loss_boolean', css_class = 'enabler'), Div('hearing_loss', css_class='dependent'),
            Field('vision_problems_boolean', css_class = 'enabler'), Div('vision_problems', css_class='dependent'),
            Field('illnesses_boolean', css_class = 'enabler'), Div('illnesses', css_class='dependent'),
            Field('services_boolean', css_class = 'enabler'), Div('services', css_class='dependent'),
            Field('worried_boolean', css_class = 'enabler'), Div('worried', css_class='dependent'),
            Field('learning_disability_boolean', css_class = 'enabler'), Div('learning_disability', css_class='dependent'),),

)

    class Meta:
        model = BackgroundInfo
        exclude = ['administration']
        
        widgets = { 
        'ear_infections': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'hearing_loss': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'vision_problems': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'illnesses': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'services': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'worried': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'learning_disability': Textarea(attrs={'cols': 80, 'rows': 3}), 
        #'birth_order': forms.NumberInput(attrs={'min':'1', 'max':'15'}),
        #'birth_weight': forms.NumberInput(attrs={'min':'1', 'max':'15', 'placeholder': 'X.X', 'step': '0.1'}),
        'due_date_diff': forms.NumberInput(attrs={'min':'1', 'max':'18'})
        }

class ContactForm(forms.Form):
    contact_name = forms.CharField(label="Your Name", required=True, max_length = 51)
    contact_email = forms.EmailField(label="Your Email Address", required=True, max_length = 101, validators = [EmailValidator()])
    contact_id = forms.CharField(label="Your Test URL", required=True, max_length = 101)
    content = forms.CharField(label="What would you like to tell us?",
        required=True,
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 6}),
        max_length = 1001
    )

    def __init__(self, *args, **kwargs):
        self.hash_id = kwargs.pop('hash_id', '')
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['contact_id'].initial='webcdi.stanford.edu/form/fill/'+self.hash_id
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(Field('contact_name'), Field('contact_email'), Field('contact_id'), Field('content'), Div(Submit('submit','Submit'), css_class="col-lg-offset-3 col-lg-9 text-center"))
