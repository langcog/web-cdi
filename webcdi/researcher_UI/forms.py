from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class AddStudyForm(forms.Form):
    name = forms.CharField(label='Study Name', max_length=51)
    instrument = forms.ModelChoiceField(queryset=instrument.objects.all(), empty_label="(choose from the list)")
    waiver = forms.CharField(widget=forms.Textarea, label='Waiver of Documentation text (no titles)', required = False)
    confirm_completion = forms.BooleanField(required = False, label="At the end of the form, would you like parents to confirm the age of their child and that they completed the entire test?<br>(Best for anonymous data collections where you haven't personally vetted each participant)")


    def __init__(self, *args, **kwargs):
        super(AddStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'add-study'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.form_method = 'post'
        self.helper.form_action = '/interface/add_study/'
#        self.helper.add_input(Submit('submit', 'Submit'))

class AddPairedStudyForm(forms.Form):
    study_group = forms.CharField(label='Study Group Name', max_length=51)
    paired_studies = forms.MultipleChoiceField(choices = [])


    def __init__(self, *args, **kwargs):
        self.your_studies = kwargs.pop('your_studies', None)
        super(AddPairedStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'add-paired-study'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.form_method = 'post'
        self.helper.form_action = '/interface/add_paired_study/'
        self.fields['paired_studies'].choices = self.your_studies
#        self.helper.add_input(Submit('submit', 'Submit'))

class RenameStudyForm(forms.Form):
    name = forms.CharField(label='Study Name', max_length=51)
    waiver = forms.CharField(widget=forms.Textarea, label='Waiver of Documentation')

    def clean(self):
        cleaned_data = super(RenameStudyForm, self).clean()
        cleaned_name = cleaned_data.get("name")
        cleaned_waiver = cleaned_data.get("waiver")

        if cleaned_data.get('cleaned_name') == '' or cleaned_data.get('cleaned_name') == self.study_name:
            print "No name input"
            no_name = True
        else:
            no_name = None

        if cleaned_data.get('cleaned_waiver') == '' or cleaned_data.get('cleaned_waiver') == self.old_waiver:
            print "No waiver input"
            no_waiver = True
        else:
            no_waiver = None

        if no_name and no_waiver:
            print "Will raise error"
            self.add_error('name', 'Both "Study Name" and "Waiver of Documentation" cannot be empty. Please update at least one field.')
            self.add_error('waiver', 'Both "Study Name" and "Waiver of Documentation" cannot be empty. Please update at least one field.')


    def __init__(self, old_study_name, *args, **kwargs):
        self.study_name = old_study_name
        self.old_waiver = kwargs.pop('study_waiver', None)
        super(RenameStudyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'rename_study'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.form_method = 'post'
        self.helper.form_action = '/interface/'+old_study_name+'rename_study/'
        self.fields['name'].initial = self.study_name
        self.fields['waiver'].initial = self.old_waiver
#        self.helper.add_input(Submit('submit', 'Submit'))
