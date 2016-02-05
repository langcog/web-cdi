from django.forms import ModelForm, Textarea
from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Field, Row, Div, HTML
from form_utils.forms import BetterModelForm
from crispy_forms.bootstrap import InlineField
from django.templatetags.static import static

from django.core.exceptions import ValidationError
import codecs, json

isoLangs = json.load(codecs.open('languages.json', 'r', 'utf-8'))
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
    child_dob = forms.DateField(input_formats=['%m/%d/%Y'], widget=forms.TextInput(attrs={'placeholder': 'mm/dd/yyyy'}), validators = [MaxValueValidator(datetime.date.today())], label = "Child DOB")
    #years = [(x,x) for x in range(1900, datetime.date.today().year+1)]
    #child_yob = forms.TypedChoiceField(label = "Child's year of birth", choices = years, coerce=int)
    #month_choices = enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

    #child_mob = forms.TypedChoiceField(label = "Child's month of birth", choices = month_choices, coerce = int) 
    child_hispanic_latino = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce = string_bool_coerce
                , required=False, label="Is your child Hispanic or Latino?")
    born_on_due_date = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, label='Was your child born early or late?', coerce=string_bool_coerce)
    early_or_late = forms.ChoiceField(
                     choices=(('early', 'Early'),('late', 'Late')), widget=forms.RadioSelect,
                 required=False)
    sex = forms.ChoiceField(
                     choices=(('M', 'Male'),('F', 'Female'), ('O', 'Other')), widget=forms.RadioSelect,
                )
    other_languages_boolean = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce=string_bool_coerce, label='Does your child regularly hear a language other than english?')

    ear_infections_boolean = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce=string_bool_coerce ,
                     label =  
                     "Has your child experienced chronic ear infections (5 or more)?"
                     )
    hearing_loss_boolean = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce=string_bool_coerce, 
                     label =  
                        'Do you suspect that your child may have hearing loss?' 
                     )
    vision_problems_boolean = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce=string_bool_coerce, 
                     label =  
                        'Is there some reason to suspect that your child may have vision problems?' 
                     )
    illnesses_boolean = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce=string_bool_coerce, 
                     label =  
                         'Has your child had any major illnesses, hospitalizations, or diagnosed disabilities?' 
                     )
    services_boolean = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce=string_bool_coerce, 
                     label =  
                        'Has your child ever received any services for speech, language, or development issues?' 
                     )
    worried_boolean = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce=string_bool_coerce, 
                     label =  
                        'Are you worried about your child\'s progress in language or communication?' 
                     )
    learning_disability_boolean = forms.TypedChoiceField(
                     choices=YESNO_CHOICES, widget=forms.RadioSelect, coerce=string_bool_coerce, 
                     label =  
                        'Have you or anyone in your immediate family been diagnosed with a language or learning disability?' 
                     )
    other_languages = forms.MultipleChoiceField(
                     choices=language_choices, 
                     label = "Which language(s)", required = False
                )
    birth_order = forms.IntegerField(widget=forms.NumberInput(attrs={'min':'1'}))

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
            if enabler_val:
                for dependent in dependents:
                    if dependent not in cleaned_data or cleaned_data.get(dependent) == '':
                        self.add_error(dependent, "This field cannot be empty")


    def __init__(self, *args, **kwargs):
        super(BackgroundForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        #self.helper.form_id = 'background_form'
        self.helper.form_class = 'form-inline'
        #self.helper.field_template = 'bootstrap3/layout/inline_field.html'
        #self.helper.help_text_inline = True
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.form_method = 'post'
        #self.helper.form_tag = False
        #self.helper.add_input(Submit('submit', 'Submit'))
        #self.helper[1:6].wrap(Fieldset, "Basic info")
        self.helper.layout = Layout(
            Fieldset( 'Basic Information', 'child_dob',HTML("<p> To preserve your privacy, we do not store the child's date of birth on our server: we only record their age in months.</p>"), 'sex','birth_order', 'birth_weight', Field('born_on_due_date', css_class='enabler'), Div('early_or_late', 'due_date_diff', css_class='dependent')),
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
        exclude = ['age', 'administration']
        #fields = '__all__'
        #fieldsets = [
        #('Basic Info', {'fields' : []}),
        #('Mother or Guardian 1', {'fields' : ['mother_yob', 'mother_education', 'mother_occupation', 'mother_hours_work']}),
        #('Father or Guardian 2', {'fields' : ['father_yob', 'father_education', 'father_occupation', 'father_hours_work']}),
        #('Income', {'fields' : ['annual_income']}),
        #('Child\'s Ethnicity', {'description': u'The following information is being collected for the sole purpose of reporting to our grant-funding institute, i.e.,  NIH (National Institute of Health).  NIH requires this information to ensure the soundness and inclusiveness of our research. Your cooperation is appreciated, but optional.', 'fields' : ['child_hispanic_latino', 'ethnicity']}),
        #('Caregiver Information', {'description': 'Approximately how many waking hours each day does your child spend with:', 'fields' : ['parent_1_hours', 'parent_2_hours', 'other', 'other_hours']}),
        #('Preschool/Daycare', {'description': 'If your child attends daycare or preschool, please fill in the following', 'fields' : ['daycare_days_per_week', 'daycare_hours_per_day', 'daycare_since']}),
        #('Language Exposure', {'description': 'If your child regularly hears a language other than English?, please fill in the following', 'fields' : ['which_language', 'language_days_per_week', 'language_hours_per_day', 'language_since', 'language_from']}),
        #('Health', {'description': 'Optional health conditions: ', 'fields' : ['ear_infections', 'hearing_loss', 'vision_problems', 'illnesses', 'services', 'worried', 'learning_disability']}),
#
#
#        ]
        widgets = { 
        'ear_infections': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'hearing_loss': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'vision_problems': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'illnesses': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'services': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'worried': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'learning_disability': Textarea(attrs={'cols': 80, 'rows': 3}), 
        }
