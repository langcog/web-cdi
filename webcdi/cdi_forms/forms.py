from django.forms import ModelForm, Textarea
from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from form_utils.forms import BetterModelForm

class BackgroundForm(BetterModelForm):
    ethnicity = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
    choices = (
    ('N', "American Indian / Alaska Native"),
    ('A', "Asian (Far East, Southeast Asia, Indian Sub-continent)"), 
    ('H', "Native Hawaiian or Other Pacific Islander"),
    ('B', "Black or African American"),
    ('W', "White"),
    ('O', "Other")), label = "My child is (check all that apply):")

    class Meta:
        model = BackgroundInfo
        #fields = '__all__'
        fieldsets = [
        ('Basic Info', {'fields' : ['age', 'gender', 'birth_order', 'birth_weight', 'early_late']}),
        ('Mother or Guardian 1', {'fields' : ['mother_yob', 'mother_education', 'mother_occupation', 'mother_hours_work']}),
        ('Father or Guardian 2', {'fields' : ['father_yob', 'father_education', 'father_occupation', 'father_hours_work']}),
        ('Income', {'fields' : ['annual_income']}),
        ('Child\'s Ethnicity', {'description': u'The following information is being collected for the sole purpose of reporting to our grant-funding institute, i.e.,  NIH (National Institute of Health).  NIH requires this information to ensure the soundness and inclusiveness of our research. Your cooperation is appreciated, but optional.', 'fields' : ['child_hispanic_latino', 'ethnicity']}),
        ('Caregiver Information', {'description': 'Approximately how many waking hours each day does your child spend with:', 'fields' : ['parent_1_hours', 'parent_2_hours', 'other', 'other_hours']}),
        ('Preschool/Daycare', {'description': 'If your child attends daycare or preschool, please fill in the following', 'fields' : ['daycare_days_per_week', 'daycare_hours_per_day', 'daycare_since']}),
        ('Language Exposure', {'description': 'If your child regularly hears a language other than English?, please fill in the following', 'fields' : ['which_language', 'language_days_per_week', 'language_hours_per_day', 'language_since', 'language_from']}),
        ('Health', {'description': 'Optional health conditions: ', 'fields' : ['ear_infections', 'hearing_loss', 'vision_problems', 'illnesses', 'services', 'worried', 'learning_disability']}),


        ]
        widgets = { 
        'ear_infections': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'hearing_loss': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'vision_problems': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'illnesses': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'services': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'worried': Textarea(attrs={'cols': 80, 'rows': 3}), 
        'learning_disability': Textarea(attrs={'cols': 80, 'rows': 3}), 
        }
