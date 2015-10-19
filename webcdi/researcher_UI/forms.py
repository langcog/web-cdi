from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class AddStudyForm(forms.Form):
    name = forms.CharField(label='Study Name', max_length=51)
    instrument = forms.ModelChoiceField(queryset=instrument.objects.all(), empty_label="(choose from the list)") 

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

