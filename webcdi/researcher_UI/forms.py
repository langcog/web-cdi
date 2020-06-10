from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div
from form_utils.forms import BetterModelForm, BetterForm
from django.urls import reverse
import os
from django.contrib.postgres.forms import IntegerRangeField
from ckeditor_uploader.widgets import CKEditorUploadingWidget

# Form for creating a new study
class AddStudyForm(BetterModelForm):
    name = forms.CharField(label='Study Name', max_length=51) # Study name
    instrument = forms.ModelChoiceField(queryset=instrument.objects.filter(language='English'), empty_label="(choose from the list)") # Study instrument (CANNOT BE CHANGED LATER)
    waiver = forms.CharField(widget=CKEditorUploadingWidget(), label='Waiver of Documentation text (no titles)', required = False) # Addition of an IRB waiver of documentation or any other instructive text can be added here
    allow_payment = forms.BooleanField(required=False, label="Would you like to pay subjects in the form of Amazon gift cards? (You will need to upload gift card codes under \"Update Study\").") # Whether study participants will be compensated in the form of gift card codes upon completion
    anon_collection = forms.BooleanField(required=False, label="Do you plan on collecting only anonymous data in this study? (e.g., posting ads on social media, mass emails, etc)") # Whether the study will have only anonymous participants (opens up a range of other settings for anonymous data collection)
    subject_cap = forms.IntegerField(label = "Maximum number of participants", required = False, min_value = 1, help_text = "Leave this blank if you do NOT want to limit the number of participants.", widget=forms.NumberInput(attrs={'placeholder': 'XXX participants'})) # If there are anonymous participants, you can set a cap that limits the number of tests that can be completed. Tests initiated before the cutoff can still be finished even after the cutoff is reached
    confirm_completion = forms.BooleanField(required = False, label="At the end of the form, would you like parents to confirm the age of their child and that they completed the entire test? (Best for anonymous data collections where you haven't personally vetted each participant)") # Asks participants to verify the child's age and that they completed the form to the best of their ability. Only for participants that have not been vetted.
    allow_sharing = forms.BooleanField(required=False, label="Would you like participants to be able to share their Web-CDI results via Facebook?") # Gives option for participants to be able to share their results via Facebook. Default off.
    test_period = forms.IntegerField(label = "# Days Before Expiration", help_text= "Between 1 and 28. Default is 14 days. (e.g., 14 = 14 days for parents to complete a form)", required = False, widget= forms.NumberInput(attrs={'placeholder':'(e.g., 14 = 14 days to complete a form)', 'min': '1', 'max': '28'})) # Number of days that a participant can use to complete an administration before expiration. By default, participants have 14 days to complete test. Ranges from 1-28 days.
    age_range = IntegerRangeField(label="Age Range For Study (in months)")
    show_feedback = forms.BooleanField(required=False, initial=True, label="Would you like to show participants graphs of their data after completion?")
    
    prefilled_data_choices = ((0, 'No, do not populate the any part of the form'), (1, 'Only the Background Information Form'), (2, 'The Background Information Form and the Vocabulary Checklist'))
    prefilled_data = forms.ChoiceField(choices = prefilled_data_choices, label = "Pre-fill data for longitudinal participants?", help_text="For longitudinal participants, would you like to populate the test with responses from earlier tests?")
    
    birth_weight_choices = (("lb", "Measure birthweight in pounds and ounces"), ("kg", "Measure birthweight in kilograms"))
    birth_weight_units = forms.ChoiceField(choices = birth_weight_choices, label = "Measurement units for birthweight")
    timing = forms.IntegerField(label="Minimum time (minutes) a parent must take to complete the study (default=6)", required=True,
        widget=forms.NumberInput(),initial=6)

    confirmation_questions = forms.BooleanField(required=False, label="Would you like participants to answer the confirmation questions (only available when split background information forms are used)")

    redirect_boolean = forms.BooleanField(label="Provide redirect button at completion of study?", required=False) # Whether to give redirect button upon completion of administration
    redirect_url = forms.URLField(label="Please enter URL", required=False)
    
    prolific_boolean = forms.BooleanField(label="Capture the Prolific Id for the participant?", required=False) # Whether to give redirect button upon completion of administration
    
    # Form validation. Form is passed automatically to views.py for higher level checking.
    def clean(self):
        cleaned_data = super(AddStudyForm, self).clean()

    # Initiating form and field layout.
    def __init__(self, *args, **kwargs):
        self.researcher = kwargs.pop('researcher', None)
        super(AddStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'add-study'
        self.helper.form_class = 'form-horizontal'
        # self.helper.template = PROJECT_ROOT + '/../cdi_forms/templates/bootstrap3/whole_uni_form.html'        
        # self.helper.template = 'bootstrap4/whole_uni_form.html'
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_method = 'post'

        if self.researcher:
            self.fields['instrument'] = forms.ModelChoiceField(queryset=instrument.objects.filter(researcher = self.researcher.researcher), empty_label="(choose from the list)")

        self.helper.form_action = reverse('add_study')
        self.helper.layout = Layout(
            Field('name'),
            Field('instrument'),
            Field('age_range'),
            Field('test_period'),
            Field('birth_weight_units'),
            Field('timing'),
            Field('waiver'),
            Field('prefilled_data'),            
            Field('allow_payment'),
            Field('anon_collection'),
            Field('subject_cap'),
            Field('confirm_completion'),
            Field('show_feedback'),
            Field('allow_sharing'),
            Field('confirmation_questions'),
            Field('redirect_boolean', css_class="css_enabler"),
            Div(Field('redirect_url'), css_class="redirect_boolean collapse"),
            Field('prolific_boolean'),
        )

    # Form is related to the study model. Exclude study group designation (is done post-creation) and researcher name (filled automatically)
    class Meta:
        model = study
        exclude = ['study_group','researcher']


# Form for grouping studies together
class AddPairedStudyForm(forms.Form):
    study_group = forms.CharField(label='Study Group Name', max_length=51) # Type out study group's name
    paired_studies = forms.ModelMultipleChoiceField(queryset=study.objects.all()) # List all studies created by researcher that are currently unpaired.

    # Form validation. The paired_studies field cannot be empty.
    def clean(self):
        cleaned_data = super(AddPairedStudyForm, self).clean()
        if not cleaned_data.get('paired_studies'):
            self.add_error('paired_studies', 'Added studies cannot be blank')

    # Form initiation. Specify form and field layout. Updated paired_studies so that only unpaired studies associated with the researcher are displayed.
    def __init__(self, *args, **kwargs):
        self.researcher = kwargs.pop('researcher', None)
        super(AddPairedStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'add-paired-study'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('add_paired_study')
        if self.researcher:
            self.fields['paired_studies'] = forms.ModelMultipleChoiceField(queryset=study.objects.filter(study_group = "", researcher = self.researcher))

# Form for updating a study. Most study settings can be updated EXCEPT FOR INSTRUMENT.
class RenameStudyForm(BetterModelForm):
    name = forms.CharField(label='Study Name', max_length=51, required=False) # Update study name
    waiver = forms.CharField(widget=CKEditorUploadingWidget, label='Waiver of Documentation', required=False)
    test_period = forms.IntegerField(label = "# Days Before Expiration", help_text= "Between 1 and 28. Default is 14 days. (e.g., 14 = 14 days for parents to complete a form)", required = False, widget= forms.NumberInput(attrs={'placeholder':'(e.g., 14 = 14 days to complete a form)', 'min': '1', 'max': '28'})) # Update testing period. Can range from 1 to 28 days.
    gift_codes = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Paste Amazon gift card codes here. Can be separated by spaces, commas, or new lines.'}), required=False, label='Gift Card Codes') # Can add a list of gift card codes (separated by new lines, commas, or spaces) to the PaymentCode model that are given out to participants upon completion of current study.
    gift_amount = forms.CharField(max_length=7, required=False, label="Amount per Card (in USD)", widget=forms.TextInput(attrs={'placeholder': '$XX.XX'})) # Specify monetary value of the list of gift card codes in the gift_codes field. Assumed that all codes in the list have the same monetary value.
    age_range = IntegerRangeField(label="Age Range For Study (in months)")

    prefilled_data_choices = ((0, 'No, do not populate the any part of the form'), (1, 'Only the Background Information Form'), (2, 'The Background Information Form and the Vocabulary Checklist'))
    prefilled_data = forms.ChoiceField(choices = prefilled_data_choices, label = "Pre-fill data for longitudinal participants?", help_text="For longitudinal participants, would you like to populate the test with responses from earlier tests?")

    birth_weight_choices = (("lb", "Measure birthweight in pounds and ounces"), ("kg", "Measure birthweight in kilograms"))
    birth_weight_units = forms.ChoiceField(choices = birth_weight_choices, label = "Measurement units for birthweight")
    
    anon_collection = forms.BooleanField(required=False, label="Do you plan on collecting only anonymous data in this study? (e.g., posting ads on social media, mass emails, etc)") # Whether the study will have only anonymous participants (opens up a range of other settings for anonymous data collection)
    allow_payment = forms.BooleanField(required=False, label="Would you like to pay subjects in the form of Amazon gift cards? (You will need to upload gift card codes under \"Update Study\").") # Whether study participants will be compensated in the form of gift card codes upon completion
    subject_cap = forms.IntegerField(label = "Maximum number of participants", required = False, min_value = 1, help_text = "Leave this blank if you do NOT want to limit the number of participants.", widget=forms.NumberInput(attrs={'placeholder': 'XXX participants'})) # If there are anonymous participants, you can set a cap that limits the number of tests that can be completed. Tests initiated before the cutoff can still be finished even after the cutoff is reached
    confirm_completion = forms.BooleanField(required = False, label="At the end of the form, would you like parents to confirm the age of their child and that they completed the entire test? (Best for anonymous data collections where you haven't personally vetted each participant)") # Asks participants to verify the child's age and that they completed the form to the best of their ability. Only for participants that have not been vetted.
    allow_sharing = forms.BooleanField(required=False, label="Would you like participants to be able to share their Web-CDI results via Facebook?") # Gives option for participants to be able to share their results via Facebook. Default off.
    show_feedback = forms.BooleanField(required=False, label="Would you like to show participants graphs of their data after completion?")
    timing = forms.IntegerField(label="Minimum time (minutes) a parent must take to complete the study (default=6)", required=True)
    confirmation_questions = forms.BooleanField(required=False, label="Would you like participants to answer the confirmation questions (only available when split background information forms are used)")
    
    redirect_boolean = forms.BooleanField(label="Provide redirect button at completion of study?", required=False) # Whether to give redirect button upon completion of administration
    redirect_url = forms.URLField(label="Please enter URL", required=False)

    prolific_boolean = forms.BooleanField(label="Capture the Prolific Id for the participant?", required=False) # Whether to give redirect button upon completion of administration
    
    # Form validation. Form is passed automatically to views.py for higher level checking.
    def clean(self):
        cleaned_data = super(RenameStudyForm, self).clean()

    # Form initiation. Specific form and field layout.
    def __init__(self, old_study_name, *args, **kwargs):
        self.age_range = kwargs.pop('age_range', None)
        super(RenameStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'rename_study'
        self.helper.form_class = 'form-horizontal'
        # self.helper.template = PROJECT_ROOT + '/../cdi_forms/templates/bootstrap3/whole_uni_form.html'        
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_method = 'post'
        if self.age_range:
            self.fields['age_range'].initial = self.age_range
        self.helper.form_action = reverse('rename_study', args=[old_study_name])
        self.helper.layout = Layout(
            Field('name'),
            Field('age_range'),
            Field('test_period'),
            Field('birth_weight_units'),
            Field('timing'),
            Field('waiver'),
            Field('prefilled_data'),
            Field('anon_collection'),
            Field('subject_cap'),
            Field('confirm_completion'),
            Field('allow_payment'),
            Div(Field('gift_codes'), css_class="gift_cards collapse"),
            Div(Field('gift_amount'), css_class="gift_cards collapse"),
            Field('show_feedback'),
            Field('allow_sharing'),
            Field('confirmation_questions'),
            Field('redirect_boolean', css_class="css_enabler"), 
            Div(Field('redirect_url'), css_class="redirect_boolean collapse"),
            Field('prolific_boolean'),
    
        )

    # Link form to study model. Exclude study group (specified in another form), researcher (automatically filled by current user), and instrument (chosen during study creation and CANNOT BE CHANGED)
    class Meta:
        model = study
        exclude = ['study_group','researcher','instrument', 'active']


class ImportDataForm(BetterForm):
    study = forms.ModelChoiceField(queryset=study.objects.all(), empty_label="(choose from the list)") # Study instrument (CANNOT BE CHANGED LATER)
    imported_file = forms.FileField()

    # Form validation. Form is passed automatically to views.py for higher level checking.
    def clean(self):
        cleaned_data = super(ImportDataForm, self).clean()
        if not cleaned_data.get('imported_file'):
            self.add_error('imported_file', 'Please upload a file.')

    # Form initiation. Specify form and field layout. Updated paired_studies so that only unpaired studies associated with the researcher are displayed.
    def __init__(self, *args, **kwargs):
        self.researcher = kwargs.pop('researcher', None)
        self.study = kwargs.pop('study', None)
        super(ImportDataForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'import-data'
        self.helper.form_class = 'form-horizontal'
        # self.helper.template = PROJECT_ROOT + '/../cdi_forms/templates/bootstrap3/whole_uni_form.html'        
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_method = 'post'
        if self.researcher:
            self.fields['study'] = forms.ModelChoiceField(queryset=study.objects.filter(researcher = self.researcher), empty_label="(choose from the list)")
        if self.study:
            self.fields['study'].initial = self.study

class EditSubjectIDForm(forms.ModelForm):
    class Meta:
        model = administration
        fields = ['subject_id', 'study']
        widgets = {
            'study' : forms.HiddenInput()
        }

    def clean(self):
        cleaned_data = super(EditSubjectIDForm,self).clean()
        if administration.objects.filter(study=cleaned_data['study'], subject_id=cleaned_data['subject_id']).exists():
            raise forms.ValidationError("An Administration with this id already exists.  Select a unique value")
        return cleaned_data

class EditLocalLabIDForm(forms.ModelForm):
    class Meta:
        model = administration
        fields = ['local_lab_id', 'study']
        widgets = {
            'study' : forms.HiddenInput()
        }

class EditOptOutForm(forms.ModelForm):
    class Meta:
        model = administration
        fields = ['opt_out', 'study']
        widgets = {
            'study' : forms.HiddenInput()
        }