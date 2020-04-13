from django import forms

from researcher_UI.models import administration
from .models import InstrumentItem

from .utils import string_bool_coerce

YESNO_CHOICES = ((False, 'No'), (True, 'Yes'))

class CatItemForm(forms.ModelForm):
    item = forms.TypedChoiceField(
        choices=YESNO_CHOICES, 
        widget=forms.RadioSelect, 
        coerce = string_bool_coerce,
        required=True, 
        label= "Does your child know?"
    )
    word = forms.ModelChoiceField(
        queryset=InstrumentItem.objects.all(),
        widget=forms.HiddenInput,
    )

    class Meta:
        model = administration
        fields = ['word','item']
        widgets = {
            'word' : forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', None)
        super().__init__(*args, **kwargs)
        try:
            self.fields['item'].label = self.context['word'].definition
        except: pass
