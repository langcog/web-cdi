from django import forms
from django.contrib.auth.models import User
from researcher_UI.models import Researcher

class ProfileForm (forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]

        
class ResearcherForm(forms.ModelForm):
    class Meta:
        model = Researcher
        exclude = ['allowed_instruments','allowed_instrument_families']
        widgets = {
            'user': forms.HiddenInput()
        }
