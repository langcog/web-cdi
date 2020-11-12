from django import forms

from researcher_UI.models import administration

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
    word_id = forms.IntegerField(
        widget=forms.HiddenInput,
    )
    label = forms.CharField(
        max_length=50,
        widget=forms.HiddenInput,
    )

    class Meta:
        model = administration
        fields = ['word_id','item','label']
        widgets = {
            'word_id' : forms.HiddenInput(),
            'label' : forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', None)
        super().__init__(*args, **kwargs)
        try:
            self.fields['item'].label = self.context['label']
        except: pass
