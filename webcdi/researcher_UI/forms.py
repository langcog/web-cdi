from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div
from form_utils.forms import BetterModelForm
from django.core.urlresolvers import reverse
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__)) # Declare project file directory

# Form for creating a new study
class AddStudyForm(BetterModelForm):
    name = forms.CharField(label='Study Name', max_length=51) # Study name
    instrument = forms.ModelChoiceField(queryset=instrument.objects.all(), empty_label="(choose from the list)") # Study instrument (CANNOT BE CHANGED LATER)
    waiver = forms.CharField(widget=forms.Textarea, label='Waiver of Documentation text (no titles)', required = False) # Addition of an IRB waiver of documentation or any other instructive text can be added here
    allow_payment = forms.BooleanField(required=False, label="Would you like to pay subjects in the form of Amazon gift cards? (You will need to upload gift card codes under \"Update Study\").") # Whether study participants will be compensated in the form of gift card codes upon completion
    anon_collection = forms.BooleanField(required=False, label="Do you plan on collecting only anonymous data in this study? (e.g., posting ads on social media, mass emails, etc)") # Whether the study will have only anonymous participants (opens up a range of other settings for anonymous data collection)
    subject_cap = forms.IntegerField(label = "Maximum number of participants", required = False, min_value = 1, help_text = "Leave this blank if you do NOT want to limit the number of participants.", widget=forms.NumberInput(attrs={'placeholder': 'XXX participants'})) # If there are anonymous participants, you can set a cap that limits the number of tests that can be completed. Tests initiated before the cutoff can still be finished even after the cutoff is reached
    confirm_completion = forms.BooleanField(required = False, label="At the end of the form, would you like parents to confirm the age of their child and that they completed the entire test? (Best for anonymous data collections where you haven't personally vetted each participant)") # Asks participants to verify the child's age and that they completed the form to the best of their ability. Only for participants that have not been vetted.
    allow_sharing = forms.BooleanField(required=False, label="Would you like participants to be able to share their Web-CDI results via Facebook?") # Gives option for participants to be able to share their results via Facebook. Default off.
    test_period = forms.IntegerField(label = "# Days Before Expiration", help_text= "Between 1 and 14. Default is 14 days. (e.g., 14 = 14 days for parents to complete a form)", required = False, widget= forms.NumberInput(attrs={'placeholder':'(e.g., 14 = 14 days to complete a form)', 'min': '1', 'max': '14'})) # Number of days that a participant can use to complete an administration before expiration. By default, participants have 14 days to complete test. Ranges from 1-14 days.

    # Initiating form and field layout.
    def __init__(self, *args, **kwargs):
        super(AddStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'add-study'
        self.helper.form_class = 'form-horizontal'
        self.helper.template = PROJECT_ROOT + '/../cdi_forms/templates/bootstrap3/whole_uni_form.html'        
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('add_study')
        self.helper.layout = Layout(
            Field('name'),
            Field('instrument'),
            Field('test_period'),
            Field('waiver'),
            Field('allow_payment'),
            Field('anon_collection'),
            Field('subject_cap'),
            Field('confirm_completion'),
            Field('allow_sharing'),
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
        self.helper.template = PROJECT_ROOT + '/../cdi_forms/templates/bootstrap3/whole_uni_form.html'        
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('add_paired_study')
        if self.researcher:
            self.fields['paired_studies'] = forms.ModelMultipleChoiceField(queryset=study.objects.filter(study_group = "", researcher = self.researcher))

# Form for updating a study. Most study settings can be updated EXCEPT FOR INSTRUMENT.
class RenameStudyForm(BetterModelForm):
    name = forms.CharField(label='Study Name', max_length=51, required=False) # Update study name
    waiver = forms.CharField(widget=forms.Textarea, label='Waiver of Documentation', required=False) # update IRB waiver of documentation
    test_period = forms.IntegerField(label = "# Days Before Expiration", help_text= "Between 1 and 14. Default is 14 days. (e.g., 14 = 14 days for parents to complete a form)", required = False, widget= forms.NumberInput(attrs={'placeholder':'(e.g., 14 = 14 days to complete a form)', 'min': '1', 'max': '14'})) # Update testing period. Can range from 1 to 14 days.
    gift_codes = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Paste Amazon gift card codes here. Can be separated by spaces, commas, or new lines.'}), required=False, label='Gift Card Codes') # Can add a list of gift card codes (separated by new lines, commas, or spaces) to the PaymentCode model that are given out to participants upon completion of current study.
    gift_amount = forms.CharField(max_length=7, required=False, label="Amount per Card (in USD)", widget=forms.TextInput(attrs={'placeholder': '$XX.XX'})) # Specify monetary value of the list of gift card codes in the gift_codes field. Assumed that all codes in the list have the same monetary value.

    # Form validation. Form is passed automatically to views.py for higher level checking.
    def clean(self):
        cleaned_data = super(RenameStudyForm, self).clean()

    # Form initiation. Specific form and field layout.
    def __init__(self, old_study_name, *args, **kwargs):
        super(RenameStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'rename_study'
        self.helper.form_class = 'form-horizontal'
        self.helper.template = PROJECT_ROOT + '/../cdi_forms/templates/bootstrap3/whole_uni_form.html'        
        self.helper.label_class = 'col-3'
        self.helper.field_class = 'col-9'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('rename_study', args=[old_study_name])
        self.helper.layout = Layout(
            Field('name'),
            Field('test_period'),
            Field('waiver'),
            Field('anon_collection'),
            Field('subject_cap'),
            Field('confirm_completion'),
            Field('allow_payment'),
            Div(Field('gift_codes'), css_class="gift_cards collapse"),
            Div(Field('gift_amount'), css_class="gift_cards collapse"),
            Field('allow_sharing'),
        )

    # Link form to study model. Exclude study group (specified in another form), researcher (automatically filled by current user), and instrument (chosen during study creation and CANNOT BE CHANGED)
    class Meta:
        model = study
        exclude = ['study_group','researcher','instrument']
