from django import forms

from django.core.exceptions import ValidationError
from brookes.models import BrookesCode


class BrookesCodeForm(forms.Form):
    code = forms.CharField(max_length=15)
    '''
    class Meta:
        model = BrookesCode
        fields = ['instrument_family','code','researcher']
        widgets = {
            'instrument_family': forms.HiddenInput(),
            'researcher': forms.HiddenInput()
        }
    '''

    
    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data['code']
        if not BrookesCode.objects.filter(code=code).exists():
            raise ValidationError('Invalid code', code='invalid')
        elif not BrookesCode.objects.filter(code=code, applied__isnull=True):
            raise ValidationError('Code already applied', code='invalid')
        return cleaned_data