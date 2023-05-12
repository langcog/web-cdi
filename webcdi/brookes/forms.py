from django import forms

from django.core.exceptions import ValidationError
from brookes.models import BrookesCode


class BrookesCodeForm(forms.Form):
    code = forms.CharField(max_length=15, required=False)
    cancel = forms.CharField(max_length=15, required=False)
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
        if cleaned_data['cancel'] != 'Cancel':
            code = cleaned_data['code']
            if not BrookesCode.objects.filter(code=code).exists():
                self.add_error('code', 'Invalid code')
                #raise ValidationError('Invalid code', code='invalid')
            elif not BrookesCode.objects.filter(code=code, applied__isnull=True):
                self.add_error('code', 'Code already applied')
                
                #raise ValidationError('Code already applied', code='invalid')
        return cleaned_data